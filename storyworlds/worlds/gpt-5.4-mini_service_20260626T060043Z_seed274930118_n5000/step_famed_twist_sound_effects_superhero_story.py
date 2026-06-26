#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero tale with a dramatic Twist and
comic-book Sound Effects.

Premise:
- A famed hero notices a problem in the city.
- A simple step-by-step rescue goes wrong when the villain causes a twist.
- The hero uses a clever move, aided by sound effects, to fix the situation.

The world simulation tracks physical meters and emotional memes so the story
prose is driven by state rather than being a frozen template.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    name: str
    setting: str
    mood: str


@dataclass
class Power:
    id: str
    label: str
    step: str
    twist: str
    sound_effects: list[str]
    meter: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class VillainPlan:
    id: str
    label: str
    trouble: str
    twist: str
    meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.step_taken: bool = False
        self.twist_seen: bool = False
        self.sound_used: bool = False

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
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.step_taken = self.step_taken
        clone.twist_seen = self.twist_seen
        clone.sound_used = self.sound_used
        clone.paragraphs = [[]]
        return clone


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    trap = world.entities.get("trap")
    if not hero or not trap:
        return out
    if hero.meters.get("trouble", 0) < THRESHOLD:
        return out
    sig = ("alarm", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    out.append("A sharp alarm chimed from above.")
    return out


CAUSAL_RULES = [ _r_alarm ]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def hero_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a famed little superhero who loved to help everyone in {world.city.name}."
    )


def setting_intro(world: World) -> None:
    world.say(
        f"The city was bright and busy, with tall buildings, busy sidewalks, and a sky that loved surprises."
    )


def power_intro(world: World, hero: Entity, power: Power) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"{hero.id} had a special power: {power.label}. When {hero.pronoun()} took a {power.step}, "
        f"the whole plan seemed ready to begin."
    )


def villain_intrusion(world: World, villain: Entity, plan: VillainPlan) -> None:
    villain.memes["trouble"] = villain.memes.get("trouble", 0) + 1
    world.say(
        f"But {villain.label} the {villain.type} was already there, planning a {plan.trouble}."
    )


def small_twist(world: World, hero: Entity, power: Power, plan: VillainPlan) -> None:
    hero.meters[power.meter] = hero.meters.get(power.meter, 0) + 1
    hero.meters["trouble"] = hero.meters.get("trouble", 0) + 1
    world.step_taken = True
    world.twist_seen = True
    world.say(
        f"{hero.id} tried the first step of the rescue, but then came a twist: {plan.twist}."
    )
    if power.sound_effects:
        world.sound_used = True
        world.say(" ".join(power.sound_effects[:2]) + "!")


def setback(world: World, hero: Entity, plan: VillainPlan) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"For a moment, everything wobbled, and {hero.id} had to think fast."
    )


def gadget_fix(world: World, hero: Entity, gadget: Gadget, power: Power) -> None:
    world.say(
        f"Then {hero.id} reached for {gadget.label} and used it exactly as planned."
    )
    hero.meters[power.effect] = 0
    hero.meters["trouble"] = max(0, hero.meters.get("trouble", 0) - 1)
    hero.memes["worry"] = max(0, hero.memes.get("worry", 0) - 1)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.sound_used = True
    world.say("Wham! Zap! Whoosh!")
    world.say(
        f"{gadget.tail.capitalize()}, and the city block grew calm again."
    )


def ending(world: World, hero: Entity, villain: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    world.say(
        f"In the end, {hero.id} stood tall, the famed hero smiling while {villain.label} was safely stopped."
    )
    world.say(
        f"The streets were quiet, the people were safe, and {world.city.name} sparkled like it had just learned a new cheer."
    )


def tell(city: City, power: Power, plan: VillainPlan, gadget: Gadget,
         hero_name: str, hero_type: str, sidekick_name: str, villain_name: str) -> World:
    world = World(city)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=["famed", "brave"]))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="boy", label=sidekick_name, traits=["helpful"]))
    villain = world.add(Entity(id="villain", kind="character", type="man", label=villain_name, traits=["sneaky"]))
    world.add(Entity(id="trap", type="thing", label="the trap", phrase="a city trap"))
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, power=power, plan=plan, gadget=gadget)

    hero_intro(world, hero)
    setting_intro(world)
    power_intro(world, hero, power)
    villain_intrusion(world, villain, plan)

    world.para()
    world.say(
        f"{sidekick.label} whispered that the hero should follow the steps carefully."
    )
    world.say(
        f"{hero.id} took one step forward, then another, but the villain's {plan.twist} made the rescue wobble."
    )
    small_twist(world, hero, power, plan)
    setback(world, hero, plan)

    world.para()
    world.say(
        f"{hero.id} remembered {gadget.label}, a gadget that could help with this exact trouble."
    )
    gadget_fix(world, hero, gadget, power)
    ending(world, hero, villain)

    return world


CITYS = {
    "metro": City(name="Metro City", setting="downtown", mood="bright"),
    "harbor": City(name="Harbor City", setting="waterfront", mood="windy"),
    "skyline": City(name="Skyline City", setting="high towers", mood="sparkling"),
}

POWERS = {
    "light": Power(
        id="light",
        label="beam of light",
        step="careful step",
        twist="a mirror twist in the alley",
        sound_effects=["Shine", "Flash"],
        meter="light",
        effect="darkness",
        tags={"light", "shine"},
    ),
    "speed": Power(
        id="speed",
        label="speed burst",
        step="quick step",
        twist="a spinning gate",
        sound_effects=["Zoom", "Vroom"],
        meter="speed",
        effect="slowdown",
        tags={"speed", "zoom"},
    ),
    "shield": Power(
        id="shield",
        label="glitter shield",
        step="steady step",
        twist="a sudden swirl of wind",
        sound_effects=["Clang", "Thunk"],
        meter="shield",
        effect="impact",
        tags={"shield", "defend"},
    ),
}

PLANS = {
    "glue": VillainPlan(id="glue", label="Glue Goblin", trouble="sticky puddle trap", twist="the floor turned sticky", meter="sticky", tags={"sticky", "trap"}),
    "fog": VillainPlan(id="fog", label="Fog Phantom", trouble="fog machine prank", twist="the whole block filled with fog", meter="fog", tags={"fog", "cloud"}),
    "kite": VillainPlan(id="kite", label="Kite Captain", trouble="kite-string snare", twist="the strings tangled around the sign", meter="tangle", tags={"tangle", "string"}),
}

GADGETS = {
    "grapple": Gadget(id="grapple", label="a grappling hook", helps={"sticky", "tangle"}, covers={"reach"}, prep="aim the hook to pull free", tail="the hook snapped the path open"),
    "lens": Gadget(id="lens", label="a bright lens", helps={"fog"}, covers={"light"}, prep="shine the lens through the haze", tail="the light cut a clean path"),
    "boots": Gadget(id="boots", label="power boots", helps={"sticky", "tangle", "fog"}, covers={"step"}, prep="step hard and stay steady", tail="the boots made every step sure", plural=True),
}

HERO_NAMES = ["Nova", "Comet", "Spark", "Ruby", "Milo", "Jett", "Iris"]
SIDEKICK_NAMES = ["Pip", "Benny", "Tia", "Lulu", "Max"]
VILLAIN_NAMES = ["Murk", "Whirl", "Snag", "Mister Hush"]


@dataclass
class StoryParams:
    city: str
    power: str
    plan: str
    gadget: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    villain_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for city in CITYS:
        for power in POWERS:
            for plan in PLANS:
                gadget = select_gadget(POWERS[power], PLANS[plan])
                if gadget:
                    out.append((city, power, plan))
    return out


def select_gadget(power: Power, plan: VillainPlan) -> Optional[Gadget]:
    for gadget in GADGETS.values():
        if plan.meter in gadget.helps:
            return gadget
    return None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes the word "step" and a dramatic twist.',
        f"Tell a famous little superhero story in {world.city.name} where {f['hero'].label} uses {f['power'].label} and must recover from a twist.",
        f'Write a bright comic-book story with Sound Effects and a happy ending after a rescue goes wrong.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    villain: Entity = f["villain"]
    power: Power = f["power"]
    plan: VillainPlan = f["plan"]
    gadget: Gadget = f["gadget"]
    return [
        QAItem(
            question=f"Who was the famed hero in the story?",
            answer=f"The famed hero was {hero.label}, the little superhero who saved {world.city.name}.",
        ),
        QAItem(
            question=f"What made the rescue turn into a twist?",
            answer=f"The rescue turned into a twist when {plan.twist} and made {hero.label}'s first step wobble.",
        ),
        QAItem(
            question=f"How did {hero.label} fix the problem?",
            answer=f"{hero.label} used {gadget.label} and {power.label} to open a safe path and stop the trouble.",
        ),
        QAItem(
            question=f"What sound effects were heard during the rescue?",
            answer=f"The story shouted comic-book sound effects like {' '.join(power.sound_effects[:2])} and Wham, Zap, Whoosh.",
        ),
        QAItem(
            question=f"Who caused the trouble?",
            answer=f"{villain.label} caused the trouble with a sneaky plan in {world.city.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses special powers and brave choices to help people.",
        ),
        QAItem(
            question="What do sound effects do in a comic story?",
            answer="Sound effects make a comic story feel loud, fast, and exciting, like the action is popping right off the page.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the problem harder or makes the story turn in a new direction.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CITYS[params.city],
        POWERS[params.power],
        PLANS[params.plan],
        GADGETS[params.gadget],
        params.hero_name,
        params.hero_type,
        params.sidekick_name,
        params.villain_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CITYS:
        lines.append(asp.fact("city", cid))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("step", pid, p.step))
        lines.append(asp.fact("twist", pid, p.twist))
        for s in p.sound_effects:
            lines.append(asp.fact("sound", pid, s))
    for vid, v in PLANS.items():
        lines.append(asp.fact("plan", vid))
        lines.append(asp.fact("trouble", vid, v.trouble))
        lines.append(asp.fact("plan_twist", vid, v.twist))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        for h in g.helps:
            lines.append(asp.fact("helps", gid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,P,L) :- city(C), power(P), plan(L).
has_gadget(P,L,G) :- gadget(G), plan(L), trouble(L,T), helps(G,T).
valid_story(C,P,L) :- valid(C,P,L), has_gadget(P,L,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with a Twist and Sound Effects.")
    ap.add_argument("--city", choices=CITYS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
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
    combos = [c for c in valid_combos()
              if (args.city is None or c[0] == args.city)
              and (args.power is None or c[1] == args.power)
              and (args.plan is None or c[2] == args.plan)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    city, power, plan = rng.choice(sorted(combos))
    gadget = args.gadget or next(g.id for g in GADGETS.values() if PLANS[plan].meter in g.helps)
    hero_type = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    villain_name = args.villain or rng.choice(VILLAIN_NAMES)
    return StoryParams(city, power, plan, gadget, hero_name, hero_type, sidekick_name, villain_name)


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
    StoryParams("metro", "light", "fog", "lens", "Nova", "girl", "Pip", "Murk"),
    StoryParams("harbor", "speed", "kite", "boots", "Comet", "boy", "Benny", "Whirl"),
    StoryParams("skyline", "shield", "glue", "grapple", "Spark", "girl", "Tia", "Snag"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
