#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sesame_ankle_intimidate_happy_ending_humor_superhero.py
=======================================================================================

A small superhero storyworld: a kid hero, a fake villain scare, a sore ankle, a
sesame-based snack or clue, and a humorous happy ending.

The seed story inspiration is a TinyStories-style superhero moment:
a child wants to be brave, someone tries to intimidate them, an ankle gets hurt
during the scramble, and the ending turns warm and funny when kindness and a
clever helper fix the day.

This world models:
- typed entities with physical meters and emotional memes,
- a causal story engine,
- a reasonableness gate,
- an inline ASP twin,
- three Q&A sets grounded in simulated state,
- a normal smoke test inside --verify.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"hurt": 0.0, "sticky": 0.0, "blocked": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "bravery": 0.0, "joy": 0.0, "relief": 0.0}

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


@dataclass
class HeroConfig:
    id: str
    type: str
    costume: str
    power: str
    title: str


@dataclass
class VillainConfig:
    id: str
    type: str
    tactic: str
    laugh: str
    label: str


@dataclass
class InjuryConfig:
    id: str
    label: str
    cause: str
    care: str
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SesameConfig:
    id: str
    label: str
    phrase: str
    snack: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RescueConfig:
    id: str
    tool: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_injury(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    ankle = world.entities.get("ankle")
    if not hero or not ankle:
        return out
    if hero.memes["fear"] >= THRESHOLD and hero.meters.get("running", 0.0) >= THRESHOLD:
        sig = ("injury", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        ankle.meters["hurt"] += 1
        hero.meters["running"] = 0.0
        out.append("__hurt__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    sidekick = world.entities.get("sidekick")
    if not hero or not sidekick:
        return out
    if hero.meters.get("hurt", 0.0) >= THRESHOLD and sidekick.meters.get("snack", 0.0) >= THRESHOLD:
        sig = ("relief", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("injury", _r_injury), Rule("relief", _r_relief)]


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


def reasonable_combo(hero: HeroConfig, villain: VillainConfig, injury: InjuryConfig, sesame: SesameConfig) -> bool:
    return "ankle" in injury.tags and "intimidate" in villain.tags and "sesame" in sesame.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for hid in HEROES:
        for vid in VILLAINS:
            for iid in INJURIES:
                for sid in SESAMES:
                    if reasonable_combo(HEROES[hid], VILLAINS[vid], INJURIES[iid], SESAMES[sid]):
                        combos.append((hid, vid, iid, sid))
    return combos


def predict(world: World, injury_id: str) -> dict:
    sim = world.copy()
    sim.get("hero").memes["fear"] += 1
    sim.get("hero").meters["running"] += 1
    propagate(sim, narrate=False)
    return {"hurt": sim.get(injury_id).meters["hurt"] >= THRESHOLD}


def start_scene(world: World, hero: Entity, sidekick: Entity, villain: Entity) -> None:
    world.say(f"{hero.id} wore a bright cape and {sidekick.id} carried a tiny bag of sesame snacks.")
    world.say(f"They patrolled the block like a pair of pocket-sized superheroes, ready for a silly adventure.")
    world.say(f"Then {villain.id} popped out with a huge grin and tried to intimidate them with {villain.attrs['line']}.")


def warn_scene(world: World, sidekick: Entity, hero: Entity, villain: Entity, injury: Entity) -> None:
    pred = predict(world, "ankle")
    sidekick.memes["bravery"] += 1
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f"{sidekick.id} blinked and said, \"That is the least scary scary face I have ever seen.\" "
        f"Still, {sidekick.pronoun()} warned {hero.id} not to run too fast, because a twisted ankle could happen."
    )


def scramble_scene(world: World, hero: Entity, villain: Entity, injury: Entity) -> None:
    hero.memes["fear"] += 1
    hero.meters["running"] += 1
    world.say(f"{hero.id} tried to dash away, but {villain.id}'s joke of a growl made the moment feel wobbly.")
    world.say(f"{hero.id}'s foot slipped on a pebble, and {hero.pronoun('possessive')} ankle gave a sharp little yelp.")


def comic_turn(world: World, sesame: Entity, sidekick: Entity, hero: Entity) -> None:
    sesame.meters["snack"] += 1
    hero.meters["hurt"] += 1
    hero.memes["fear"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{sidekick.id} opened the sesame snack bag with a dramatic whisper: \"Behold, emergency fuel!\" "
        f"{hero.id} took a bite and started laughing at the crunch."
    )


def rescue_scene(world: World, rescuer: Entity, rescue: Entity, hero: Entity, injury: Entity) -> None:
    rescuer.meters["help"] += 1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{rescuer.id} helped {hero.id} sit down, wrapped the ankle with a soft scarf, and said "
        f"that even superheroes sometimes needed a break."
    )
    world.say(
        f"Then {rescue.id} arrived with a tiny ice pack shaped like a star, and the whole scene looked more funny than fierce."
    )


def ending_scene(world: World, hero: Entity, sidekick: Entity, villain: Entity, sesame: Entity) -> None:
    world.say(
        f"{villain.id} tried one last intimidating pose, but {hero.id} just lifted the sesame bag like a trophy and said, "
        f"\"We are undefeated by crunch.\""
    )
    world.say(
        f"{sidekick.id} laughed so hard that even {villain.id} cracked up, and the three of them shared sesame snacks on the steps."
    )
    world.say(
        f"By sunset, {hero.id} was walking again with a tiny limp and a bigger smile, while {hero.pronoun('possessive')} cape fluttered like a banner."
    )


def tell(hero_cfg: HeroConfig, villain_cfg: VillainConfig, injury_cfg: InjuryConfig, sesame_cfg: SesameConfig, rescue_cfg: RescueConfig) -> World:
    world = World()
    hero = world.add(Entity(id=hero_cfg.id, kind="character", type=hero_cfg.type, role="hero", label=hero_cfg.title))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="girl", role="helper"))
    villain = world.add(Entity(id=villain_cfg.id, kind="character", type=villain_cfg.type, role="villain", attrs={"line": villain_cfg.laugh}))
    ankle = world.add(Entity(id="ankle", kind="thing", type="bodypart", label="ankle"))
    sesame = world.add(Entity(id="sesame", kind="thing", type="snack", label=sesame_cfg.label))
    rescue = world.add(Entity(id="rescue", kind="thing", type="tool", label=rescue_cfg.tool))

    hero.memes["bravery"] = 1.0
    sidekick.meters["snack"] = 0.0
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, ankle=ankle, sesame=sesame, rescue=rescue, injury_cfg=injury_cfg, sesame_cfg=sesame_cfg, rescue_cfg=rescue_cfg)

    start_scene(world, hero, sidekick, villain)
    world.para()
    warn_scene(world, sidekick, hero, villain, ankle)
    scramble_scene(world, hero, villain, ankle)
    world.para()
    comic_turn(world, sesame, sidekick, hero)
    rescue_scene(world, sidekick, rescue, hero, ankle)
    ending_scene(world, hero, sidekick, villain, sesame)
    world.facts["outcome"] = "happy"
    return world


HEROES = {
    "cap": HeroConfig(id="CapKid", type="boy", costume="red cape", power="quick grin", title="Captain Bright"),
    "spark": HeroConfig(id="Spark", type="girl", costume="blue mask", power="kind courage", title="Spark Hero"),
    "zoom": HeroConfig(id="Zoomer", type="boy", costume="yellow scarf", power="fast feet", title="Zoom Hero"),
}

VILLAINS = {
    "bluster": VillainConfig(id="Bluster", type="boy", tactic="intimidate", laugh="I am the scary-est!", label="bluster"),
    "mug": VillainConfig(id="Mugsy", type="boy", tactic="intimidate", laugh="Boo! I am almost alarming!", label="mug"),
}

INJURIES = {
    "ankle": InjuryConfig(id="ankle", label="ankle", cause="slip", care="rest", line="ouch", tags={"ankle"}),
}

SESAMES = {
    "snack": SesameConfig(id="sesame", label="sesame snack", phrase="a bag of sesame snacks", snack="crunch", clue="sesame", tags={"sesame"}),
    "seed": SesameConfig(id="sesame_seed", label="sesame seed trail", phrase="a trail of sesame seeds", snack="trail", clue="sesame", tags={"sesame"}),
}

RESCUES = {
    "ice": RescueConfig(id="ice", tool="ice pack", action="cool", result="cool"),
}


@dataclass
class StoryParams:
    hero: str
    villain: str
    injury: str
    sesame: str
    rescue: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with humor and a happy ending.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--injury", choices=INJURIES)
    ap.add_argument("--sesame", choices=SESAMES)
    ap.add_argument("--rescue", choices=RESCUES)
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
    if not combos:
        raise StoryError("No valid superhero story combinations exist.")
    filtered = [
        c for c in combos
        if (args.hero is None or c[0] == args.hero)
        and (args.villain is None or c[1] == args.villain)
        and (args.injury is None or c[2] == args.injury)
        and (args.sesame is None or c[3] == args.sesame)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    hero, villain, injury, sesame = rng.choice(sorted(filtered))
    rescue = args.rescue or "ice"
    return StoryParams(hero=hero, villain=villain, injury=injury, sesame=sesame, rescue=rescue)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story that includes the words "{f["sesame_cfg"].clue}", "ankle", and "intimidate".',
        f"Tell a funny superhero story where {f['hero'].id} gets a sore ankle after someone tries to intimidate them, but the ending is happy.",
        f"Write a child-friendly superhero story with a joke, a small injury, sesame snacks, and a brave helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    villain = f["villain"]
    sesame = f["sesame_cfg"]
    qas = [
        QAItem(
            question="Why did the hero stop running?",
            answer=f"{hero.id} stopped because {hero.pronoun('possessive')} ankle hurt after the scramble. The intimidating pose made the moment feel tense, but the sore ankle made the hero sit down."
        ),
        QAItem(
            question="How did the story stay funny?",
            answer=f"The villain's intimidating act turned out silly, and the sesame snacks became emergency fuel. Everyone ended up laughing instead of being afraid."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{hero.id} went from wobbly and sore to smiling and walking again. The sesame snack, the helper, and the tiny ice pack turned the scary moment into a happy ending."
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sesame?",
            answer="Sesame can mean tiny seeds or snacks made from them. They are small, crunchy, and tasty."
        ),
        QAItem(
            question="What should you do if your ankle hurts?",
            answer="Rest it and ask a grown-up for help. A hurt ankle needs care so it can heal."
        ),
        QAItem(
            question="What does intimidate mean?",
            answer="To intimidate someone means to try to scare them into feeling small. Brave people can stay calm and keep going."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES or params.villain not in VILLAINS or params.injury not in INJURIES or params.sesame not in SESAMES or params.rescue not in RESCUES:
        raise StoryError("Invalid story parameters.")
    world = tell(HEROES[params.hero], VILLAINS[params.villain], INJURIES[params.injury], SESAMES[params.sesame], RESCUES[params.rescue])
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
valid(H,V,I,S) :- hero(H), villain(V), injury(I), sesame(S), has_ankle(I), intimidates(V), has_sesame(S).
happy_end(H) :- valid(H,_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in HEROES:
        lines.append(asp.fact("hero", k))
    for k in VILLAINS:
        lines.append(asp.fact("villain", k))
        lines.append(asp.fact("intimidates", k))
    for k in INJURIES:
        lines.append(asp.fact("injury", k))
        lines.append(asp.fact("has_ankle", k))
    for k in SESAMES:
        lines.append(asp.fact("sesame", k))
        lines.append(asp.fact("has_sesame", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(hero=None, villain=None, injury=None, sesame=None, rescue=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(hero="cap", villain="bluster", injury="ankle", sesame="snack", rescue="ice", seed=1),
    StoryParams(hero="spark", villain="mug", injury="ankle", sesame="seed", rescue="ice", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(rng_base + i))
            params.seed = rng_base + i
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
