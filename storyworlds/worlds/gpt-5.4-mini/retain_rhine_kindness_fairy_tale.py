#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/retain_rhine_kindness_fairy_tale.py
====================================================================

A small fairy-tale storyworld about a child, a river, and a kindness charm that
must be retained through a windy day on the Rhine.

Seed words:
- retain
- rhine
- kindness

This world makes a tiny classical simulation:
- typed entities with physical meters and emotional memes
- a hazard / tension / turn / resolution story
- a Python reasonableness gate and an inline ASP twin
- three QA sets grounded in world state, not by parsing story text

The tale pattern:
A child carries a kindness charm to the Rhine. Wind and water try to take it
away. A helper act of kindness restores the charm, and the ending proves the
kindness was retained.
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
RETAIN_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "fairy"}
        male = {"boy", "father", "dad", "man", "king", "fisherman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    glow: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tension:
    id: str
    label: str
    cause: str
    fix: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_waver(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["danger"] < THRESHOLD:
            continue
        sig = ("waver", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("__waver__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("waver", "social", _r_waver), Rule("kindness", "social", _r_kindness)]


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


def retain_holds(charm: Charm, tension: Tension, effort: int) -> bool:
    return tension.power + effort <= 3 and charm.fragile


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, t in TENSIONS.items():
            if t.power <= 3:
                combos.append((sid, tid))
    return combos


def make_rhyme_line(place: str) -> str:
    return {
        "meadow": "The grass was green, and the day was kind.",
        "bridge": "The bridge arched high, like a sleepy silver smile.",
        "mill": "The mill sang softly beside the water.",
    }.get(place, "The day was soft and bright.")


def predict_turn(world: World, tension: Tension) -> dict:
    sim = world.copy()
    _do_tension(sim, sim.get("charm"), tension, narrate=False)
    return {"danger": sim.get("charm").meters["danger"], "worry": sim.get("hero").memes["worry"]}


def _do_tension(world: World, charm_ent: Entity, tension: Tension, narrate: bool = True) -> None:
    charm_ent.meters["danger"] += tension.power
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, helper: Entity, charm: Charm) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a fair morning, {hero.id} walked toward the Rhine with {helper.id}. "
        f"{make_rhyme_line(world.setting.id)}"
    )
    world.say(
        f"In {hero.pronoun('possessive')} pocket, {hero.pronoun('possessive')} kept "
        f"{charm.phrase}, a little charm meant to retain kindness."
    )


def tension_beat(world: World, hero: Entity, helper: Entity, tension: Tension, charm: Charm) -> None:
    world.say(
        f"Then {tension.cause} came along the river path. {hero.id} peered down and "
        f"saw {charm.label} trembling in the breeze."
    )
    pred = predict_turn(world, tension)
    hero.memes["worry"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'"We must retain it," whispered {helper.id}. '
        f'"If it slips away, the kindness may be hard to keep."'
    )


def lose_or_waver(world: World, hero: Entity, helper: Entity, tension: Tension) -> None:
    hero.meters["danger"] += tension.power
    helper.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A gust tugged at the ribbon, and the charm skittered near the water. "
        f"{hero.id} reached fast, and {helper.id} stepped closer so it would not be lost."
    )


def rescue(world: World, hero: Entity, helper: Entity, charm_ent: Entity, tension: Tension) -> None:
    charm_ent.meters["danger"] = 0.0
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"Together they caught the ribbon before the Rhine could take it. "
        f"Then {helper.id} tied it to a willow twig, and the charm glimmered safe again."
    )
    world.say(
        f"The wind still whispered, but now the charm could be retained, and its soft glow stayed bright."
    )


def lesson(world: World, hero: Entity, helper: Entity, charm: Charm, tension: Tension) -> None:
    hero.memes["peace"] += 1
    helper.memes["peace"] += 1
    world.say(
        f"{hero.id} smiled and said, 'Kindness is not something to drop by the river.' "
        f"{helper.id} nodded, and the two of them promised to keep it close."
    )
    world.say(
        f"By the time the sun touched the Rhine, {charm.label} was still there, glowing softly like a tiny star."
    )


def tell(setting: Setting, charm: Charm, tension: Tension,
         hero_name: str = "Mira", hero_gender: str = "girl",
         helper_name: str = "Nico", helper_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Mother", kind="character", type=parent_type, role="parent", label="the mother"))
    charm_ent = world.add(Entity(id="charm", type="thing", label=charm.label))
    world.facts["parent"] = parent
    world.facts["charm"] = charm
    world.facts["setting"] = setting
    world.facts["tension"] = tension

    setup(world, hero, helper, charm)
    world.para()
    tension_beat(world, hero, helper, tension, charm)
    lose_or_waver(world, hero, helper, tension)
    world.para()
    rescue(world, hero, helper, charm_ent, tension)
    lesson(world, hero, helper, charm, tension)

    world.facts.update(hero=hero, helper=helper, charm_ent=charm_ent, outcome="retained")
    return world


SETTINGS = {
    "meadow": Setting("meadow", "the meadow by the Rhine", "bright"),
    "bridge": Setting("bridge", "the old bridge over the Rhine", "windy"),
    "mill": Setting("mill", "the mill path beside the Rhine", "gentle"),
}

CHARMS = {
    "heart": Charm("heart", "a heart charm", "a tiny heart charm", "shone warm"),
    "ribbon": Charm("ribbon", "a kindness ribbon", "a kindness ribbon", "shimmered silver"),
    "bell": Charm("bell", "a little bell charm", "a little bell charm", "rang like dew"),
}

TENSIONS = {
    "gust": Tension("gust", "a windy gust", "the wind rushed hard", "a steady hand", 1, tags={"wind"}),
    "splash": Tension("splash", "a splash from the river", "the water leapt up", "a quick step back", 2, tags={"water"}),
    "twist": Tension("twist", "a twist of the ribbon", "the ribbon snagged on bark", "a careful tug", 1, tags={"ribbon"}),
}

GIRL_NAMES = ["Mira", "Ella", "Luna", "Asha", "Nia", "Faye"]
BOY_NAMES = ["Nico", "Owen", "Jules", "Theo", "Eli", "Finn"]
TRAITS = ["gentle", "brave", "kind", "careful"]


@dataclass
class StoryParams:
    setting: str
    charm: str
    tension: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kindness": [("What is kindness?", "Kindness means choosing to help, share, or care for someone in a warm and gentle way.")],
    "rhine": [("What is the Rhine?", "The Rhine is a long river. Rivers carry water across the land and can have windy paths beside them.")],
    "wind": [("What can wind do?", "Wind can tug at ribbons, hats, and paper. It can make a small thing feel wobbly.")],
    "water": [("Why can water be tricky near a river?", "Water can move fast and surprise you. A careful step keeps little things safe near the edge.")],
    "retail": [("What does retain mean?", "Retain means to keep something and not let it slip away.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    tension = f["tension"]
    charm = f["charm"]
    return [
        f'Write a fairy tale for a small child that includes the words "retain" and "Rhine".',
        f"Tell a gentle story where {hero.id} tries to retain {charm.label} near the Rhine while {tension.label.lower()} causes trouble.",
        f"Write a magical kindness story with a river, a charm, and a safe ending where the charm stays with the child.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    charm = f["charm"]
    tension = f["tension"]
    parent = f["parent"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {helper.id}, who walked to the Rhine with a kind little charm. Their {parent.label_word} is part of the family world, too, because the story keeps the kindness close and safe."
        ),
        QAItem(
            question="What did the children want to do?",
            answer=f"They wanted to retain {charm.label} and keep it from slipping away. They also wanted the charm to keep its gentle magic while they walked by the river."
        ),
        QAItem(
            question=f"What caused trouble near the Rhine?",
            answer=f"{tension.cause.capitalize()} caused trouble. That made {hero.id} worry, because the charm could have been lost if they had not held it fast."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"{helper.id} helped {hero.id} catch the ribbon and tie it to a willow twig. That simple kindness kept the charm safe and let them retain it."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["charm"].tags) | set(world.facts["tension"].tags)
    tags |= {"kindness", "rhine", "retail"}
    out: list[QAItem] = []
    for tag in ["kindness", "rhine", "wind", "water", "retail"]:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.charm in CHARMS and params.tension in TENSIONS


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen river trouble is too strong for a gentle fairy tale ending. Pick a lighter tension.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(Unknown setting.)")
    if args.charm and args.charm not in CHARMS:
        raise StoryError("(Unknown charm.)")
    if args.tension and args.tension not in TENSIONS:
        raise StoryError("(Unknown tension.)")
    combos = [(s, c, t) for s in SETTINGS for c in CHARMS for t in TENSIONS if TENSIONS[t].power <= 2]
    if args.setting:
        combos = [x for x in combos if x[0] == args.setting]
    if args.charm:
        combos = [x for x in combos if x[1] == args.charm]
    if args.tension:
        combos = [x for x in combos if x[2] == args.tension]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, tension = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (BOY_NAMES if helper_gender == "boy" else GIRL_NAMES) if n != hero_name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, charm, tension, hero_name, hero_gender, helper_name, helper_gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHARMS[params.charm], TENSIONS[params.tension],
                 params.hero_name, params.hero_gender, params.helper_name, params.helper_gender,
                 params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about retain, Rhine, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--tension", choices=TENSIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


ASP_RULES = r"""
valid(S, C, T) :- setting(S), charm(C), tension(T), weak_tension(T).
retained(T) :- chosen_tension(T), weak_tension(T).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    for tid, t in TENSIONS.items():
        lines.append(asp.fact("tension", tid))
        if t.power <= 2:
            lines.append(asp.fact("weak_tension", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams("meadow", "heart", "gust", "Mira", "girl", "Nico", "boy", "mother", "gentle"),
    StoryParams("bridge", "ribbon", "splash", "Ella", "girl", "Finn", "boy", "father", "careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(f"{a}" for a in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
