#!/usr/bin/env python3
"""
storyworlds/worlds/reindeer_delicious_minimize_twist_cautionary_folk_tale.py
=============================================================================

A small folk-tale storyworld about a reindeer, a delicious temptation, and the
need to minimize a risky choice.

Seed tale sketch:
---
In a snow-bright village, a young reindeer loved the smell of delicious honey
cakes cooling by the hearth. One windy evening, the reindeer wanted to carry the
cakes across a frozen path to a lantern circle, but the wise elder warned that
too much hurry would make the cakes slide and spill. The reindeer ignored the
warning, took a bouncing shortcut, and the tray twisted in the wind.

At the last moment, the reindeer learned to slow down, lower the tray, and take
small careful steps. The cakes stayed whole, the lantern circle was fed, and the
reindeer learned to minimize haste when something delicious was in its hooves.

World updates:
---
    desire for delicious thing  -> joy + desire + 1
    risky carrying on ice       -> wobble + 1
    wobble + haste              -> spill risk increases
    careful slowing             -> wobble decreases
    careful delivery            -> gift delivered + calm + love

Narrative instruments:
---
    Twist      -> the apparent shortcut turns out to be the source of the trouble,
                  and the fix comes from choosing the slower, kinder path.
    Cautionary -> the story explicitly teaches a small lesson about restraint and
                  minimizing careless motion near something precious.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "reindeer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the snowy lane"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    dangerous_on: str


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        return w


SETTINGS = {
    "village": Setting(place="the snowy village", affords={"carry"}),
    "forest": Setting(place="the pine forest", affords={"carry"}),
    "hill": Setting(place="the windy hill", affords={"carry"}),
}

ACTIVITIES = {
    "carry": Activity(
        id="carry",
        verb="carry the delicious cakes",
        gerund="carrying the delicious cakes",
        rush="rush across the ice",
        risk="the cakes could slip and spill",
        weather="winter",
        keyword="delicious",
        tags={"delicious", "ice", "cautionary"},
    ),
    "share": Activity(
        id="share",
        verb="share the delicious berries",
        gerund="sharing the delicious berries",
        rush="grab them all at once",
        risk="the berries could tumble into the snow",
        weather="winter",
        keyword="delicious",
        tags={"delicious", "berries", "cautionary"},
    ),
}

PRIZES = {
    "cakes": Prize(
        label="cakes",
        phrase="a tray of delicious honey cakes",
        type="cakes",
        dangerous_on="ice",
    ),
    "berries": Prize(
        label="berries",
        phrase="a basket of delicious red berries",
        type="berries",
        dangerous_on="ice",
    ),
}

GEAR = [
    Gear(
        id="cloth",
        label="a warm cloth wrap",
        prep="wrap the tray in a warm cloth and walk slowly",
        tail="walked carefully with the warm cloth wrap",
        guards={"ice"},
    ),
]

NAMES = ["Bran", "Edda", "Lumi", "Nico", "Sora", "Tavi"]
TRAITS = ["careful", "curious", "gentle", "bold", "small", "bright"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


class ReindeerWorld:
    pass


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if act.keyword == "delicious" and prize.dangerous_on == "ice":
                    combos.append((place, aid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world about reindeer, delicious things, and minimizing risk.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait)


def _do_activity(world: World, hero: Entity, act: Activity, prize: Entity, narrate: bool = True) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.meters["wobble"] = hero.meters.get("wobble", 0.0) + 1
    if narrate:
        world.say(f"{hero.id} wanted to {act.verb} because the smell was delicious.")
        world.say(f"But {hero.pronoun('possessive')} hooves felt slick on the ice.")


def predict_spill(world: World, hero: Entity, act: Activity, prize: Entity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), act, sim.get(prize.id), narrate=False)
    return sim.get(hero.id).meters.get("wobble", 0.0) >= THRESHOLD


def tell(setting: Setting, act: Activity, prize_cfg: Prize, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="reindeer", label=name, memes={"care": 0.0}))
    elder = world.add(Entity(id="Elder", kind="character", type="reindeer", label="the elder", memes={"wisdom": 1.0}))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    gear = world.add(Entity(id="Cloth", type="gear", label=GEAR[0].label, owner=hero.id))

    world.say(f"{hero.id} was a {trait} little reindeer who lived near {setting.place}.")
    world.say(f"{hero.id} loved the {prize_cfg.phrase} because they were delicious.")
    world.say(f"Every winter evening, {hero.id} wondered whether to take the tray to the lantern circle.")

    world.para()
    world.say(f"One cold dusk, {hero.id} and {elder.label} stood beside the frozen path.")
    if predict_spill(world, hero, act, prize):
        world.say(f'"You must minimize the hurry," {elder.label} said. "If you rush, {act.risk}."')
    _do_activity(world, hero, act, prize, narrate=True)

    world.para()
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"{hero.id} ignored the warning and tried to {act.rush}.")
    world.say("Then came a little twist: the shortest path looked fastest, but it was the slickest ice of all.")
    hero.meters["wobble"] = hero.meters.get("wobble", 0.0) + 1
    if hero.meters["wobble"] >= THRESHOLD:
        world.say(f"The tray tipped, and {act.risk}.")
        world.say(f"{elder.label} did not scold. {elder.label} only said, 'Slow steps save something delicious.'")

    world.para()
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1
    world.say(f"{hero.id} lowered the tray, took the warm cloth wrap, and chose careful steps.")
    world.say(f"They {GEAR[0].tail}, and the cakes stayed neat for the lantern circle.")
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(f"In the end, {hero.id} learned to minimize haste when carrying something delicious across ice.")

    world.facts.update(hero=hero, elder=elder, prize=prize, act=act, setting=setting, gear=gear, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["act"], f["prize"]
    return [
        f'Write a short folk tale about a reindeer named {hero.id} and something delicious that must be carried carefully.',
        f"Tell a cautionary story where {hero.id} wants to {act.verb} but learns to minimize haste on the ice.",
        f'Write a gentle tale with a twist about {hero.id}, the {prize.label}, and a wise elder who warns about rushing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, act = f["hero"], f["elder"], f["prize"], f["act"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {act.verb} because it smelled delicious.",
        ),
        QAItem(
            question=f"Why did {elder.label} warn {hero.id}?",
            answer=f"{elder.label} warned {hero.id} because rushing on the ice could make {act.risk}.",
        ),
        QAItem(
            question="What twist changed the ending?",
            answer="The shortcut that looked easiest was the slickest ice, so the safe answer was to slow down instead.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} used a warm cloth wrap, took careful steps, and carried the delicious {prize.label} safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does minimize mean?",
            answer="To minimize something means to make it as small as possible, like making a mistake or a mess smaller.",
        ),
        QAItem(
            question="What is a cautionary tale?",
            answer="A cautionary tale is a story that gently warns someone about a risky choice so they can learn to be careful.",
        ),
        QAItem(
            question="What is a reindeer?",
            answer="A reindeer is a deer that lives in cold places and can walk through snow with steady hooves.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story q&a ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world q&a ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in s.affords:
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("dangerous_on", pid, p.dangerous_on))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,Pr) :- affords(P,A), keyword(A,"delicious"), dangerous_on(Pr,"ice").
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(p - a))
    print(" only in clingo:", sorted(a - p))
    return 1


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("village", "carry", "cakes", "Bran", "careful"),
            StoryParams("forest", "share", "berries", "Edda", "gentle"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
