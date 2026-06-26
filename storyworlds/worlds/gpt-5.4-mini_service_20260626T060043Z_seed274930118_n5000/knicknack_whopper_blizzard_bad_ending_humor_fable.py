#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/knicknack_whopper_blizzard_bad_ending_humor_fable.py
===============================================================================================================================

A small fable-like storyworld about a blizzard, a tempting whopper, and a
cherished knicknack. The stories are short, child-facing, and state-driven, but
they intentionally keep a light, humorous, bad-ending shape: the hero's pride
wins, then the blizzard wins harder.

Seed inspiration:
---
A fox finds a shiny knicknack in a blizzard and tells a whopper about how brave
and clever it is. A crow warns that vanity is a slippery hill. The fox laughs,
keeps boasting, and marches into the snow to prove itself. The knicknack is
lost, the whopper is exposed, and the fox ends the day cold, embarrassed, and
empty-pawed.

World model:
---
- The world has a single setting and one risky weather event: a blizzard.
- A hero can carry a knicknack, tell a whopper, and refuse a wiser helper.
- Pride raises risk; cold meters and wind meters can drop the knicknack.
- A warning may be ignored, which turns into embarrassment and loss.
- The ending is "bad" in a fable sense: the lesson is clear, but the hero
  does not recover what was lost.
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
    carried_by: Optional[str] = None
    protected: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old lane"
    indoors: bool = False


@dataclass
class Hazard:
    id: str
    weather: str
    cold_risk: float
    wind_risk: float
    visibility_loss: float
    keyword: str = "blizzard"


@dataclass
class Knicknack:
    id: str
    label: str
    phrase: str
    kind: str = "knicknack"
    fragile: bool = True
    shiny: bool = True


@dataclass
class Whopper:
    id: str
    label: str
    line: str
    tell_risk: float = 1.0


@dataclass
class Helper:
    id: str
    label: str
    advice: str
    caution: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting, hazard: Hazard) -> None:
        self.setting = setting
        self.hazard = hazard
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.setting, self.hazard)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_chill(world: World) -> list[str]:
    out: list[str] = []
    if world.hazard.weather != "blizzard":
        return out
    for actor in world.characters():
        if actor.meters.get("out_in_blizzard", 0.0) < THRESHOLD:
            continue
        sig = ("chill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["cold"] = actor.meters.get("cold", 0.0) + world.hazard.cold_risk
        actor.meters["wind"] = actor.meters.get("wind", 0.0) + world.hazard.wind_risk
        out.append(f"The wind snapped at {actor.id} like a teasing mouth.")
    return out


def _r_blind_lost(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("cold", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.owner != actor.id or item.carried_by != actor.id:
                continue
            if item.protected:
                continue
            sig = ("lost", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if actor.meters.get("pride", 0.0) >= THRESHOLD:
                item.carried_by = None
                actor.meters["loss"] = actor.meters.get("loss", 0.0) + 1
                out.append(f"In the white swirl, {item.label} slipped away without a sound.")
    return out


def _r_embarrass(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("whopper_told", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("loss", 0.0) < THRESHOLD:
            continue
        sig = ("embarrass", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["embarrassment"] = actor.memes.get("embarrassment", 0.0) + 1
        out.append(f"That left {actor.id} with a cold face and a very small story.")
    return out


CAUSAL_RULES = [_r_chill, _r_blind_lost, _r_embarrass]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def forecast_loss(world: World, actor: Entity, item: Entity) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["out_in_blizzard"] = 1.0
    propagate(sim, narrate=False)
    return bool(sim.get(item.id).meters.get("loss", 0.0) >= THRESHOLD)


def fable_moral() -> str:
    return "A loud boast can vanish faster than a footprint in fresh snow."


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a small {hero.type} who liked shiny things and big words."
    )
    world.say(
        f"{helper.id} watched the lane and preferred quiet sense to noisy pride."
    )


def find_knicknack(world: World, hero: Entity, item: Entity) -> None:
    hero.meters["delight"] = hero.meters.get("delight", 0.0) + 1
    item.carried_by = hero.id
    world.say(
        f"One day {hero.id} found {item.phrase} near the gate and tucked {item.pronoun('object')} close."
    )


def tell_whopper(world: World, hero: Entity, whopper: Whopper) -> None:
    hero.memes["whopper_told"] = hero.memes.get("whopper_told", 0.0) + 1
    hero.meters["pride"] = hero.meters.get("pride", 0.0) + 1
    world.say(
        f"{hero.id} laughed and told a whopper: \"{whopper.line}\""
    )


def warn(world: World, helper: Entity, hero: Entity, item: Entity) -> None:
    if forecast_loss(world, hero, item):
        world.facts["warned"] = True
        world.say(
            f"\"That snow is no joke,\" said {helper.id}. \"Keep your eyes open, or the blizzard will blink first.\""
        )


def ignore_warning(world: World, hero: Entity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(
        f"{hero.id} snorted, as if a blizzard were only a fluffy curtain in a tall tale."
    )


def enter_blizzard(world: World, hero: Entity) -> None:
    hero.meters["out_in_blizzard"] = hero.meters.get("out_in_blizzard", 0.0) + 1
    world.say(
        f"Then {hero.id} marched out into the blizzard to prove {hero.pronoun('possessive')} whopper."
    )
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, item: Entity, helper: Entity) -> None:
    if item.carried_by is None:
        world.say(
            f"When the snow settled, {hero.id} had no {item.label} and no clever ending, only a cold nose and a smaller grin."
        )
    else:
        world.say(
            f"When the snow settled, {hero.id} still had {item.pronoun('object')}, but the lesson was lost in the wind."
        )
    world.say(
        f"{helper.id} shook {helper.id}'s head and said, \"Big words do not keep little treasures warm.\""
    )
    world.say(fable_moral())


def tell(setting: Setting, hazard: Hazard, hero_name: str = "Pip", helper_name: str = "Moss") -> World:
    world = World(setting, hazard)

    hero = world.add(Entity(id=hero_name, kind="character", type="fox"))
    helper = world.add(Entity(id=helper_name, kind="character", type="crow"))
    item = world.add(Entity(
        id="knicknack",
        label="knicknack",
        phrase="a tiny brass knicknack",
        owner=hero.id,
        carried_by=None,
    ))
    whopper = Whopper(
        id="whopper",
        label="whopper",
        line="I can outshine the storm and dance through any snowdrift!",
    )

    world.facts.update(hero=hero, helper=helper, item=item, whopper=whopper, setting=setting, hazard=hazard)

    introduce(world, hero, helper)
    world.para()
    find_knicknack(world, hero, item)
    tell_whopper(world, hero, whopper)
    warn(world, helper, hero, item)
    ignore_warning(world, hero)
    world.para()
    enter_blizzard(world, hero)
    world.para()
    ending(world, hero, item, helper)
    world.facts["lost"] = item.carried_by is None
    return world


SETTINGS = {
    "lane": Setting(place="the old lane", indoors=False),
    "orchard": Setting(place="the orchard edge", indoors=False),
    "hill": Setting(place="the little hill", indoors=False),
}

HAZARDS = {
    "blizzard": Hazard(
        id="blizzard",
        weather="blizzard",
        cold_risk=1.0,
        wind_risk=1.0,
        visibility_loss=1.0,
        keyword="blizzard",
    ),
}

KNICKKNACKS = {
    "brass": Knicknack(
        id="brass",
        label="knicknack",
        phrase="a tiny brass knicknack",
    ),
}

HELPERS = {
    "crow": Helper(
        id="crow",
        label="crow",
        advice="keep your feet under you and your pride behind you",
        caution="the white wind can hide a hole in the ground",
        tags={"fable", "warning"},
    ),
}

WHOPPERS = {
    "brag": Whopper(
        id="brag",
        label="whopper",
        line="I can outshine the storm and dance through any snowdrift!",
    ),
}


@dataclass
class StoryParams:
    place: str
    hazard: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, h) for p in SETTINGS for h in HAZARDS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    hazard: Hazard = f["hazard"]
    return [
        f'Write a short fable for a young child that uses the words "knicknack", "whopper", and "blizzard".',
        f"Tell a humorous fable about {hero.id}, a proud fox, and {helper.id}, a careful crow, on a {hazard.keyword}.",
        f"Write a tiny moral story where a character loses a knicknack after telling a whopper in the snow.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    whopper: Whopper = f["whopper"]
    qa = [
        QAItem(
            question=f"Who found the knicknack in the story?",
            answer=f"{hero.id} found the tiny brass knicknack and tucked it close at first.",
        ),
        QAItem(
            question=f"What whopper did {hero.id} tell?",
            answer=f"{hero.id} told this whopper: \"{whopper.line}\"",
        ),
        QAItem(
            question=f"Who warned {hero.id} about the blizzard?",
            answer=f"{helper.id} the crow warned {hero.id} to be careful in the snow.",
        ),
    ]
    if f.get("lost"):
        qa.append(
            QAItem(
                question=f"What happened to the knicknack by the end?",
                answer=f"The knicknack was lost in the blizzard, and {hero.id} ended with only a cold nose and an embarrassed grin.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blizzard?",
            answer="A blizzard is a very strong snowstorm with wind and blowing snow that can make it hard to see.",
        ),
        QAItem(
            question="What is a whopper?",
            answer="A whopper is a very big lie or a very big story that is not true.",
        ),
        QAItem(
            question="What is a knicknack?",
            answer="A knicknack is a small decorative object, often a little thing people keep on a shelf or carry because they like it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H), type(H,fox).
helper(C) :- character(C), type(C,crow).

whopper_told(H) :- tells_whopper(H).
pride(H) :- tells_whopper(H), blizzard(B), enters(H,B).

at_risk(I) :- item(I), blizzard(B), enters(_,B), carries(_,I).

lost(I) :- at_risk(I), pride(H), carries(H,I).
embarrassed(H) :- lost(I), tells_whopper(H).

#show at_risk/1.
#show lost/1.
#show embarrassed/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("weather", hid, h.weather))
    for kid, k in KNICKKNACKS.items():
        lines.append(asp.fact("item", kid))
    for cid, c in HELPERS.items():
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("type", cid, "crow"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Lightweight parity check: Python gate says every combo is valid; ASP should
    # at least parse and yield a stable empty/ground result for the shown atoms.
    try:
        asp.one_model(asp_program("#show lost/1."))
    except Exception as exc:
        print(f"ASP error: {exc}")
        return 1
    print(f"OK: ASP program loaded for {len(valid_combos())} valid setting/hazard combos.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like blizzard storyworld with a knicknack and a whopper.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    place = args.place or rng.choice([c[0] for c in combos])
    hazard = args.hazard or rng.choice([c[1] for c in combos])
    if (place, hazard) not in combos:
        raise StoryError("No valid combination matches the requested setting and hazard.")
    hero_name = args.name or rng.choice(["Pip", "Milo", "Fenn", "Nim", "Toby"])
    helper_name = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, hazard=hazard, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], HAZARDS[params.hazard], params.hero_name, params.helper_name)
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


CURATED = [
    StoryParams(place="lane", hazard="blizzard", hero_name="Pip", helper_name="crow"),
    StoryParams(place="orchard", hazard="blizzard", hero_name="Milo", helper_name="crow"),
    StoryParams(place="hill", hazard="blizzard", hero_name="Fenn", helper_name="crow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show lost/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show lost/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name} at {p.place} ({p.hazard})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
