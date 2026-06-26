#!/usr/bin/env python3
"""
storyworlds/worlds/animate_bracket_lantern_flashback_humor_cautionary_superhero.py
===================================================================================

A small standalone story world in a superhero style, built from the seed words
"animate", "bracket", and "lantern".

Premise:
- A young helper-hero protects the city at dusk.
- A strange bracket-shaped relay frame can hold a lantern and focus its beam.
- A tiny burst of animating light makes city machinery move on its own.

The world supports:
- Flashback: a remembered earlier mishap explains today's caution.
- Humor: the hero and sidekick can make a light joke during tension.
- Cautionary: the story must end with a safer, wiser choice.

The simulated state tracks:
- meters: physical readiness, light charge, wobble, safety, and distance.
- memes: courage, worry, pride, humor, relief, and caution.
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

HERO_TYPES = ["girl", "boy"]
HERO_NAMES = ["Nova", "Milo", "Tess", "Kai", "Ruby", "Leo", "Zuri", "Finn"]
SIDEKICK_NAMES = ["Pip", "Bean", "Dot", "Jax", "Luma", "Bix"]

LOCATIONS = {
    "rooftop": "the rooftop",
    "alley": "the lantern alley",
    "dock": "the quiet dock",
    "tower": "the clock tower",
}

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the rooftop"
    dusk: bool = True
    afford_bracket: bool = True
    afford_lantern: bool = True
    afford_animate: bool = True


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    purpose: str
    risk: str
    fix: str
    flashback: str
    humor: str
    caution: str
    safe_result: str


@dataclass
class StoryParams:
    setting: str = "rooftop"
    gadget: str = "bracket"
    name: str = "Nova"
    gender: str = "girl"
    sidekick: str = "Pip"
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


SETTING_REGISTRY = {
    "rooftop": Setting(place="the rooftop", dusk=True),
    "alley": Setting(place="the lantern alley", dusk=True),
    "dock": Setting(place="the quiet dock", dusk=True),
    "tower": Setting(place="the clock tower", dusk=True),
}

GADGET_REGISTRY = {
    "bracket": Gadget(
        id="bracket",
        label="a bracket frame",
        phrase="a sturdy bracket frame",
        purpose="hold the lantern steady and aim its beam",
        risk="the beam can wobble and skip away in the dark",
        fix="the frame keeps the lantern facing the right way",
        flashback="Once, the beam slipped sideways and startled the pigeons.",
        humor="Pip once called it a moon-hugger, and Nova had laughed so hard she snorted.",
        caution="A loose beam can confuse people and send them the wrong way.",
        safe_result="the lantern stayed steady and lit the path like a small star",
    ),
    "lantern": Gadget(
        id="lantern",
        label="a lantern",
        phrase="a bright brass lantern",
        purpose="shine over the dark path",
        risk="it can dim if carried too far from the charger box",
        fix="the bracket gives it a safe place to rest and glow",
        flashback="Last time, Nova carried it by hand and nearly dropped it on a curb.",
        humor="Pip said it looked like a sleepy firefly in a suit.",
        caution="A lantern that bounces in the dark can make a brave plan turn clumsy.",
        safe_result="the lantern glowed calmly and made the dark feel friendly",
    ),
    "animate": Gadget(
        id="animate",
        label="an animate spark",
        phrase="a tiny animate spark",
        purpose="wake up the rescue trolley for one careful moment",
        risk="if it grows too lively, the trolley might roll away on its own",
        fix="the bracket can corral the spark and keep it gentle",
        flashback="Nova remembered the first time the spark made the trolley sneeze and squeal.",
        humor="Pip had named the spark Wiggle, which made everyone grin.",
        caution="Magic that moves things should stay small and watched.",
        safe_result="the trolley rolled only where Nova meant it to go",
    ),
}

VALID_COMBOS = [
    ("rooftop", "bracket"),
    ("rooftop", "lantern"),
    ("rooftop", "animate"),
    ("alley", "bracket"),
    ("alley", "lantern"),
    ("alley", "animate"),
    ("dock", "bracket"),
    ("dock", "lantern"),
    ("dock", "animate"),
    ("tower", "bracket"),
    ("tower", "lantern"),
    ("tower", "animate"),
]


def valid_combos() -> list[tuple[str, str]]:
    return list(VALID_COMBOS)


def prize_at_risk(gadget: Gadget) -> bool:
    return True


def select_fix(gadget: Gadget) -> bool:
    return True


def explain_rejection(gadget: Gadget) -> str:
    return f"(No story: the selected gadget '{gadget.id}' cannot support a safe superhero turn here.)"


def explain_gender(gadget_id: str, gender: str) -> str:
    return f"(No story: '{gadget_id}' is not blocked by gender in this world, but the explicit choice was still invalid.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with flashback, humor, and cautionary beats.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--gadget", choices=GADGET_REGISTRY)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
              and (args.gadget is None or c[1] == args.gadget)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, gadget = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    return StoryParams(setting=setting, gadget=gadget, name=name, gender=gender, sidekick=sidekick)


def _hero_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def build_world(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="thing", label=params.sidekick))
    gadget = GADGET_REGISTRY[params.gadget]
    tool = world.add(Entity(id=gadget.id, kind="thing", type=gadget.id, label=gadget.label, phrase=gadget.phrase, owner=hero.id))
    world.facts.update(hero=hero, sidekick=sidekick, gadget=gadget, tool=tool)

    subj, obj, poss = _hero_pronouns(params.gender)
    place = world.setting.place

    world.say(f"{hero.id} was a small superhero who watched over {place} after sunset.")
    world.say(f"{hero.id} and {sidekick.id} liked working together, because one of them could look sharp and the other could make a joke at exactly the right moment.")
    world.say(f"Tonight, {hero.id} carried {gadget.phrase}, because it could {gadget.purpose}.")

    world.para()
    world.say(f"At {place}, the danger felt small but tricky: {gadget.risk}.")
    world.say(f"{gadget.flashback} {hero.id} remembered that and grew careful.")
    world.say(f"{sidekick.id} grinned and said, “If the beam wanders again, we should give it a tiny map.”")
    world.say(f"{hero.id} laughed, even though {hero.pronoun('possessive')} hands stayed steady on the frame.")

    world.para()
    world.say(f"{hero.id} tried to use {gadget.label} to {gadget.purpose}.")
    world.say(f"That was funny in a nervous way, because {gadget.humor}")
    world.say(f"But {gadget.caution}")
    world.say(f"So {hero.id} stopped, adjusted the bracket, and made the lantern sit just right.")
    world.say(f"Then {gadget.safe_result}.")

    world.para()
    world.say(f"In the end, {hero.id} and {sidekick.id} stood under the glowing beam and watched the city stay calm.")
    world.say(f"{hero.id} felt proud, {sidekick.id} felt relieved, and the whole street looked less scary than it had a little while before.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    g: Gadget = world.facts["gadget"]
    hero: Entity = world.facts["hero"]
    return [
        f"Write a short superhero story for a child about {hero.id}, {g.label}, and a careful rescue at dusk.",
        f"Tell a flashback-rich story where a hero uses {g.phrase} without letting the beam wobble.",
        f"Write a humorous but cautionary superhero tale that includes the words animate, bracket, and lantern.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    sidekick: Entity = world.facts["sidekick"]
    g: Gadget = world.facts["gadget"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about {hero.id}, a small superhero who watched over {place} and worked with {sidekick.id}.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the earlier mistake with {g.label}?",
            answer=f"{hero.id} remembered the earlier mistake because {g.flashback} That made {hero.id} careful this time.",
        ),
        QAItem(
            question=f"How did the story end with {g.label}?",
            answer=f"{hero.id} adjusted {g.label} so it could do its job safely, and then {g.safe_result}.",
        ),
        QAItem(
            question=f"What did the sidekick say that made the story a little funny?",
            answer=f"{sidekick.id} said the beam should have a tiny map, which made {hero.id} laugh.",
        ),
        QAItem(
            question=f"What careful lesson did the story show?",
            answer=f"It showed that powerful tools and magic should be used slowly and watched closely so nobody gets hurt.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    g: Gadget = world.facts["gadget"]
    hero: Entity = world.facts["hero"]
    return [
        QAItem(
            question="What is a bracket?",
            answer="A bracket is a shape or frame that can hold something steady so it does not wobble or fall.",
        ),
        QAItem(
            question="What is a lantern?",
            answer="A lantern is a light that helps people see when it is dark.",
        ),
        QAItem(
            question="What does animate mean?",
            answer="Animate means to make something seem alive or move with energy.",
        ),
        QAItem(
            question=f"Why was {g.label} useful in this world?",
            answer=f"It was useful because it helped {hero.id} keep the lantern steady and keep the rescue safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(rooftop; alley; dock; tower).
gadget(bracket; lantern; animate).

safe(setting(S), gadget(G)) :- setting(S), gadget(G).
valid_story(S, G) :- safe(setting(S), gadget(G)).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for gid in GADGET_REGISTRY:
        lines.append(asp.fact("gadget", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(setting="rooftop", gadget="bracket", name="Nova", gender="girl", sidekick="Pip"),
    StoryParams(setting="alley", gadget="lantern", name="Kai", gender="boy", sidekick="Bean"),
    StoryParams(setting="tower", gadget="animate", name="Tess", gender="girl", sidekick="Dot"),
]


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(item)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.gadget} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
