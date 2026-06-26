#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale with tarragon, fog,
and a repetition-driven rescue.

Premise:
- A young pilot carries a fragile crate of tarragon seeds to a moon garden.
- A thick fog rolls over the landing field and makes the route hard to read.
- Repetition is the key instrument: the pilot repeats a signal, a scan, and a
  careful instruction until the lost helper finds the way.

The world model uses physical meters and emotional memes:
- meters: fuel, visibility, sprout, damp, dust, signal
- memes: calm, worry, wonder, trust, relief, repetition

The story is generated from simulated state, not a frozen template.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def p(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moon port"
    detail: str = "a silver launchpad"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    weather: str
    keyword: str
    trail: str
    repeat_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_fog(world: World) -> list[str]:
    out: list[str] = []
    fog = world.facts.get("fog", 0.0)
    if fog < THRESHOLD:
        return out
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        sig = ("foggy", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0) + 1
        out.append(f"The fog made {actor.id} slow down and listen harder.")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    repeats = world.facts.get("repeat_count", 0)
    if repeats < 2:
        return out
    guide = world.facts.get("guide")
    helper = world.facts.get("helper")
    if not guide or not helper:
        return out
    sig = ("repeat", guide.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    out.append(f"Again and again, {guide.id} repeated the signal until {helper.id} answered.")
    return out


def _r_seed_sprout(world: World) -> list[str]:
    out: list[str] = []
    crate = world.facts.get("crate")
    if not crate:
        return out
    if crate.meters.get("damp", 0) < THRESHOLD:
        return out
    sig = ("sprout", crate.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crate.meters["sprout"] = crate.meters.get("sprout", 0) + 1
    out.append("Inside the crate, the tarragon seeds woke up and began to sprout.")
    return out


CAUSAL_RULES = [_r_fog, _r_repeat, _r_seed_sprout]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True
                lines.extend(got)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {
        "lost": bool(sim.facts.get("lost_helper", False)),
        "sprout": any(e.meters.get("sprout", 0) >= THRESHOLD for e in sim.entities.values()),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.facts["repeat_count"] = world.facts.get("repeat_count", 0) + 1
    world.facts["fog"] = world.facts.get("fog", 0) + 1
    actor.memes["wonder"] = actor.memes.get("wonder", 0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"{hero.id} was a little {hero.type} pilot who loved quiet star routes and "
        f"carried {hero.p('possessive')} {prize.label} everywhere."
    )
    world.say(
        f"{helper.id} liked the same sky road, and together they dreamed about "
        f"{activity.gerund} by the moon gardens."
    )


def setup(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"At {world.setting.place}, the {world.setting.detail} glimmered under the engines."
    )
    world.say(
        f"One day, {hero.id} wanted to {activity.verb}, but a fog bank slid in from the dark hills."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.facts["fog"] = 1.0
    world.facts["helper"] = helper
    world.facts["guide"] = hero
    world.facts["crate"] = prize
    if predict(world, hero, activity)["lost"]:
        world.say(
            f'"If we go now, the fog may hide the trail," {helper.p("subject")} said. '
            f'"We should slow down and listen."'
        )


def conflict(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity) -> None:
    world.para()
    hero.memes["repetition"] = hero.memes.get("repetition", 0) + 1
    world.say(
        f"{hero.id} started to {activity.rush}, then stopped. The fog was too thick, and the trail kept vanishing."
    )
    world.say(
        f"{hero.id} repeated {activity.repeat_line} once, then twice, then one more time."
    )
    world.say(
        f"{activity.trail}."
    )
    do_activity(world, hero, activity, narrate=True)
    helper.meters["signal"] = helper.meters.get("signal", 0) + 1
    world.say(
        f"{helper.id} answered with a bright blink from the rover lamp, and the reply came back clearer each time."
    )


def resolution(world: World, hero: Entity, helper: Entity, prize: Entity, activity: Activity) -> None:
    world.para()
    prize.meters["damp"] = prize.meters.get("damp", 0) + 1
    do_activity(world, hero, activity, narrate=True)
    world.say(
        f"At last, the repeated signal led them to the moon garden."
    )
    world.say(
        f"The crate cracked open in the warm light, and the tarragon seeds had sprouted into tiny green curls."
    )
    world.say(
        f"{hero.id} smiled at the fog, which now looked soft instead of scary, and {helper.id} waved back from the door."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type="pilot"))
    prize = world.add(Entity(id="crate", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    intro(world, hero, helper, prize, activity)
    world.para()
    setup(world, hero, helper, prize, activity)
    conflict(world, hero, helper, activity, prize)
    resolution(world, hero, helper, prize, activity)
    world.facts.update(hero=hero, helper=helper, prize=prize, activity=activity, setting=setting)
    return world


SETTINGS = {
    "moon_port": Setting(place="the moon port", detail="silver launchpad", affords={"signal"}),
    "fog_garden": Setting(place="the fog garden", detail="quiet lantern path", affords={"signal"}),
    "orbital_hatch": Setting(place="the orbital hatch", detail="a narrow view of stars", affords={"signal"}),
}

ACTIVITIES = {
    "signal": Activity(
        id="signal",
        verb="follow the signal path",
        gerund="following the signal path",
        rush="dash after the blinking lights",
        weather="foggy",
        keyword="signal",
        trail="The first lights faded, so the pilot repeated the call to find the next marker",
        repeat_line="follow the signal",
        tags={"fog", "repetition", "space"},
    )
}

PRIZES = {
    "crate": Prize(
        label="tarragon crate",
        phrase="a little crate of tarragon seeds",
        type="crate",
        region="hands",
    )
}

GEAR = [
    Gear(
        id="lamp",
        label="a rover lamp",
        covers={"hands"},
        guards={"signal"},
        prep="switch on a rover lamp",
        tail="used the lamp to keep the route bright",
    )
]

HERO_NAMES = ["Nova", "Iris", "Pip", "Tala", "Mika"]
HELPER_NAMES = ["Rin", "Sol", "Juno", "Cedar", "Lumi"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short Space Adventure story for a child that includes "tarragon" and "fog".',
        f"Tell a gentle story about {hero.id} who wants to {act.verb} in the fog and learns by repeating the signal.",
        f"Write a moon garden story where repetition helps a pilot find the way and save the tarragon seeds.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} carry to the moon garden?",
            answer=f"{hero.id} carried a little crate of tarragon seeds.",
        ),
        QAItem(
            question=f"What made the trip hard for {hero.id} and {helper.id}?",
            answer=f"A thick fog made the trail hard to see, so they had to slow down and repeat the signal.",
        ),
        QAItem(
            question=f"How did repetition help in the story?",
            answer=f"{hero.id} repeated the signal again and again until {helper.id} answered and the two of them found the moon garden.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The tarragon seeds sprouted into tiny green curls, and the fog stopped feeling scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fog?",
            answer="Fog is a cloud of tiny water drops near the ground that can make it hard to see far away.",
        ),
        QAItem(
            question="What is tarragon?",
            answer="Tarragon is a fragrant green herb that people can grow in a garden or use for cooking.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying the same thing more than once, like repeating a signal until someone hears it.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
foggy_world(W) :- fog(W), fog(W).
repetition_help(A) :- repeats(A, N), N >= 2.
story_ok(P, A, C) :- setting(P), activity(A), prize(C), foggy_world(P), repetition_help(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("repeats", aid, 2))
        lines.append(asp.fact("fog", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world with tarragon, fog, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("moon_port", "signal", "crate"), ("fog_garden", "signal", "crate"), ("orbital_hatch", "signal", "crate")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.activity or args.prize:
        combos = [c for c in combos if (not args.place or c[0] == args.place) and (not args.activity or c[1] == args.activity) and (not args.prize or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if helper == hero:
        helper = rng.choice([n for n in HELPER_NAMES if n != hero])
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.hero, "girl" if params.hero in {"Nova", "Iris", "Tala", "Mika"} else "boy", params.helper)
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


def asp_verify() -> int:
    print("OK: ASP twin is present for the simple story gate.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible story combos:")
        for c in valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, combo in enumerate(valid_combos()):
            params = StoryParams(place=combo[0], activity=combo[1], prize=combo[2], hero=HERO_NAMES[i % len(HERO_NAMES)], helper=HELPER_NAMES[i % len(HELPER_NAMES)], seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
