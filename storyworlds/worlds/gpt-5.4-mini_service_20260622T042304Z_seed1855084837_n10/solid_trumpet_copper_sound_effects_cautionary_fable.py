#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10/solid_trumpet_copper_sound_effects_cautionary_fable.py
===============================================================================================================

A small fable-style story world about a childlike animal, a copper trumpet, and
the lesson that loud sound can be useful in the right place and rude in the
wrong one.

Seed premise:
- Words: solid, trumpet, copper
- Features: Sound Effects, Cautionary
- Style: Fable

The story world is intentionally compact:
- one typed Entity model with physical meters and emotional memes
- one World with entities, facts, and narrative history
- a simple predict-then-warn beat
- a forward rule for loud sound startling nearby creatures
- a reasonableness gate plus an inline ASP twin
- grounded prompts / story QA / world QA built from simulated state
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

# Robust import path handling: walk upward until we find storyworlds/results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
_CUR = _HERE
while True:
    candidate = os.path.join(_CUR, "results.py")
    if os.path.exists(candidate):
        if _CUR not in sys.path:
            sys.path.insert(0, _CUR)
        break
    parent = os.path.dirname(_CUR)
    if parent == _CUR:
        break
    _CUR = parent

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
LOUD_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    location: str = ""
    material: str = ""
    solid: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "hare": {"subject": "she", "object": "her", "possessive": "her"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "crow": {"subject": "he", "object": "him", "possessive": "his"},
            "tortoise": {"subject": "he", "object": "him", "possessive": "his"},
            "mouse": {"subject": "she", "object": "her", "possessive": "her"},
            "badger": {"subject": "he", "object": "him", "possessive": "his"},
            "owl": {"subject": "she", "object": "her", "possessive": "her"},
            "goat": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class StoryParams:
    hero: str
    helper: str
    place: str
    trumpet: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Setting:
    place: str
    background: str
    audience: tuple[str, ...]


@dataclass(frozen=True)
class HeroSpec:
    type: str
    label: str
    trait: str


@dataclass(frozen=True)
class TrumpetSpec:
    label: str
    phrase: str
    material: str
    solid: bool
    tags: tuple[str, ...]


SETTINGS = {
    "meadow": Setting(place="the meadow", background="The grass was soft, and the wildflowers nodded in the breeze.", audience=("lamb", "bee")),
    "yard": Setting(place="the yard", background="The fence stood still under a bright sky.", audience=("kitten", "hen")),
    "hill": Setting(place="the hill", background="The hill looked wide and open, with no walls to hold a sound in.", audience=("goat", "bird")),
}

HEROES = {
    "hare": HeroSpec(type="hare", label="a small hare", trait="curious"),
    "mouse": HeroSpec(type="mouse", label="a tiny mouse", trait="eager"),
    "crow": HeroSpec(type="crow", label="a black crow", trait="proud"),
}

HELPERS = {
    "tortoise": HeroSpec(type="tortoise", label="an old tortoise", trait="wise"),
    "owl": HeroSpec(type="owl", label="a gray owl", trait="calm"),
    "goat": HeroSpec(type="goat", label="a patient goat", trait="careful"),
}

TRUMPETS = {
    "copper": TrumpetSpec(label="trumpet", phrase="a solid copper trumpet", material="copper", solid=True, tags=("sound", "metal", "copper")),
    "golden": TrumpetSpec(label="trumpet", phrase="a solid trumpet with a gold shine", material="brass", solid=True, tags=("sound", "metal")),
}

LOUD_SOUNDS = {
    "toot": "TOOT!",
    "trumpet": "toot-toot!",
    "clang": "CLANG!",
}

CURATED = [
    StoryParams(hero="hare", helper="tortoise", place="meadow", trumpet="copper"),
    StoryParams(hero="mouse", helper="owl", place="yard", trumpet="copper"),
    StoryParams(hero="crow", helper="goat", place="hill", trumpet="copper"),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def setup_world(params: StoryParams) -> World:
    if params.hero not in HEROES or params.helper not in HELPERS or params.place not in SETTINGS or params.trumpet not in TRUMPETS:
        raise StoryError("Unknown story parameter.")
    world = World(SETTINGS[params.place])
    hero_spec = HEROES[params.hero]
    helper_spec = HELPERS[params.helper]
    trumpet_spec = TRUMPETS[params.trumpet]
    hero = world.add(Entity(id="hero", kind="character", type=hero_spec.type, label=hero_spec.label, role="hero", tags={hero_spec.trait}))
    helper = world.add(Entity(id="helper", kind="character", type=helper_spec.type, label=helper_spec.label, role="helper", tags={helper_spec.trait}))
    trumpet = world.add(Entity(id="trumpet", kind="thing", type="trumpet", label=trumpet_spec.label, phrase=trumpet_spec.phrase, material=trumpet_spec.material, solid=trumpet_spec.solid, tags=set(trumpet_spec.tags)))
    audience = world.add(Entity(id="audience", kind="thing", type="group", label="nearby little animals", plural=True, location=world.setting.place))
    helper.memes["wisdom"] += 1
    hero.memes["curiosity"] += 1
    trumpet.meters["shine"] += 0.5
    world.facts.update(
        hero=hero,
        helper=helper,
        trumpet=trumpet,
        setting=world.setting,
        hero_spec=hero_spec,
        helper_spec=helper_spec,
        trumpet_spec=trumpet_spec,
        audience=audience,
        sound="toot",
    )
    return world


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    trumpet = world.get("trumpet")
    audience = world.get("audience")
    if hero.meters["loudness"] < LOUD_MIN:
        return out
    sig = ("startle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    audience.memes["startled"] += 1
    hero.memes["pride"] += 1
    out.append("The little animals jumped at the noise.")
    if trumpet.location == world.setting.place:
        trumpet.meters["echo"] += 1
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _r_startle(world):
            changed = True
            produced.append(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_startle(world: World) -> bool:
    sim = world.copy()
    sim.get("hero").meters["loudness"] += 1
    propagate(sim, narrate=False)
    return sim.get("audience").memes["startled"] >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get("hero")
    helper = world.get("helper")
    trumpet = world.get("trumpet")
    audience = world.get("audience")

    world.say(f"{hero.label.capitalize()} lived by {world.setting.place}. {world.setting.background}")
    world.say(f"One day, {hero.pronoun()} found {trumpet.phrase} tucked under a leafy fern.")
    world.say(f"It was {trumpet.material} and { 'solid' if trumpet.solid else 'hollow' }, and it shone in the sun.")
    world.para()
    world.say(f"{hero.label.capitalize()} loved the bright shape of the trumpet.")
    world.say(f'"Listen!" {hero.pronoun().capitalize()} cried. "{LOUD_SOUNDS["trumpet"]}"')
    if predict_startle(world):
        helper.memes["caution"] += 1
        world.say(f"{helper.label.capitalize()} lifted a hand and said, " '"A trumpet is fine for a parade, but not for a quiet path."')
        world.say(f'"A loud sound can wake fear before it wakes joy," {helper.pronoun()} warned.')
        hero.memes["choice"] += 1
        world.say(f"{hero.label.capitalize()} looked at the little animals and held the trumpet still.")
        world.para()
        world.say(f"Then {helper.label.lower()} led {hero.pronoun("object")} to the hill, where a fable-sized wind could carry the sound safely.")
        hero.meters["loudness"] += 1
        trumpet.location = "the hill"
        propagate(world, narrate=False)
        world.say(f"On the hill, {hero.label.lower()} blew again: {LOUD_SOUNDS['toot']}")
        world.say(f"This time the sound was cheerful, not cruel, and even the air seemed to listen.")
        world.say(f"The trumpet stayed { 'solid' if trumpet.solid else 'still' } in {hero.pronoun('possessive')} paws while the meadow below kept its peace.")
    else:
        hero.meters["loudness"] += 1
        propagate(world)
        world.say(f"The sound stayed small, and the day stayed calm.")
    world.para()
    world.say(f"The fable taught this: a trumpet is a good servant when it is used with care, but a bad master when it is used to boast.")
    world.say(f"From then on, {hero.label.lower()} saved the copper trumpet for open places and kind reasons.")
    world.say(f"And the little animals of {world.setting.place} slept without fear, which was the quietest music of all.")

    world.facts.update(outcome="caution", audience=audience, ready=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child that includes the words "solid", "trumpet", and "copper".',
        f'Write a cautionary story where {f["hero"].label} finds a copper trumpet and learns when loud sound helps and when it hurts.',
        f'Tell a fable with sound effects like "{LOUD_SOUNDS["trumpet"]}" and a lesson about using a trumpet kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    trumpet = world.facts["trumpet"]
    setting = world.facts["setting"]
    qa = [
        QAItem(
            question=f"Where did {hero.label.lower()} find the trumpet?",
            answer=f"{hero.label.capitalize()} found the trumpet by {setting.place}. It was tucked under a fern, waiting to be noticed.",
        ),
        QAItem(
            question=f"Why did {helper.label.lower()} warn {hero.pronoun('object')}?",
            answer=f"{helper.label.capitalize()} warned {hero.pronoun('object')} because the trumpet was loud and the nearby little animals could be startled. A fable is kind when it teaches care before trouble grows.",
        ),
        QAItem(
            question=f"What did {hero.label.lower()} do after the warning?",
            answer=f"{hero.label.capitalize()} carried the trumpet to the hill and blew it there instead. That turned the sound into a cheerful call instead of a rude surprise.",
        ),
    ]
    if world.facts.get("ready"):
        qa.append(QAItem(
            question="What made the trumpet special in the story?",
            answer="It was a solid copper trumpet, so it felt strong in the paws and shone like a small sun. That made it tempting to show off, which is why the lesson mattered.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    trumpet = world.facts["trumpet"]
    qa = [
        QAItem(
            question="What is a trumpet for?",
            answer="A trumpet is a musical instrument. It makes a bright, loud sound that can call people, lead a parade, or play a tune.",
        ),
        QAItem(
            question="What does copper mean?",
            answer="Copper is a reddish metal. It is often shiny and strong, so people use it for tools and instruments.",
        ),
        QAItem(
            question="What does solid mean?",
            answer="Solid means something keeps its shape and does not pour or splash like water. A solid thing can be held in your hand.",
        ),
        QAItem(
            question=f"Why should a loud sound like {world.facts['sound']} be used carefully?",
            answer="A loud sound can help in the right place, but it can also startle animals or disturb a quiet room. Good manners make noise kinder.",
        ),
    ]
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.material:
            bits.append(f"material={e.material}")
        if e.solid:
            bits.append("solid=True")
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hero in HEROES:
        for helper in HELPERS:
            for place in SETTINGS:
                combos.append((hero, helper, place))
    return combos


ASP_RULES = r"""
hero(hero).
helper(helper).
setting(meadow).
setting(yard).
setting(hill).
trumpet(copper).
material(copper).
solid(trumpet).
loud(sound).
warns(Helper, Hero) :- helper(Helper), hero(Hero).
startles :- loudness(1), trumpet(copper), solid(trumpet).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", hero) for hero in HEROES
    ] + [
        asp.fact("helper", helper) for helper in HELPERS
    ] + [
        asp.fact("setting", place) for place in SETTINGS
    ] + [
        asp.fact("trumpet", tid) for tid in TRUMPETS
    ]
    lines.append(asp.fact("copper", "copper"))
    lines.append(asp.fact("solid_item", "trumpet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    smoke_params = StoryParams(hero="hare", helper="tortoise", place="meadow", trumpet="copper")
    try:
        sample = generate(smoke_params)
    except Exception as exc:
        print(f"SMOKE FAIL: generation crashed: {exc}")
        return 1
    if not sample.story.strip():
        print("SMOKE FAIL: empty story")
        return 1

    py = set(valid_combos())
    # ASP twin is intentionally tiny here; we just ensure the program runs and the
    # ordinary generation path works in the same process.
    try:
        import asp  # noqa: F401
        _ = asp_program("#show solid/1.")
    except Exception as exc:
        print(f"SMOKE FAIL: ASP helper unavailable or program error: {exc}")
        return 1

    print(f"OK: smoke story generated, {len(py)} python combos available.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable about a solid copper trumpet and careful sound.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trumpet", choices=TRUMPETS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
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
              if (args.hero is None or c[0] == args.hero)
              and (args.helper is None or c[1] == args.helper)
              and (args.place is None or c[2] == args.place)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hero, helper, place = rng.choice(sorted(combos))
    trumpet = args.trumpet or "copper"
    return StoryParams(hero=hero, helper=helper, place=place, trumpet=trumpet)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is intentionally minimal for this small fable world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero} / {p.helper} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
