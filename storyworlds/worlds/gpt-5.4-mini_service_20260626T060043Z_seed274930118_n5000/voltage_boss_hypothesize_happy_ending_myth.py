#!/usr/bin/env python3
"""
A standalone storyworld: a mythic little tale about a village, a bossy storm,
a brave hypothesize moment, and a happy ending powered by voltage.
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
    meter: float = 0.0
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "god", "boss"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    boss_name: str
    storm_name: str
    relic: str
    seed: Optional[int] = None


PLACES = {
    "mountain": "a high mountain shrine",
    "valley": "a green valley village",
    "cave": "a deep echoing cave",
    "shore": "a bright shore temple",
}

HERO_NAMES = ["Mira", "Taro", "Lina", "Soren", "Nia", "Ivo"]
BOSS_NAMES = ["Boros", "Kara", "Orun", "Vel", "Dama"]
STORM_NAMES = ["Thunder-Hound", "Sky-Boss", "Storm-King", "Cloud-Chief"]
RELICS = ["lantern", "bell", "drum", "crown", "harp"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_overcharge(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    relic = world.entities["relic"]
    if hero.meters.get("voltage", 0.0) >= THRESHOLD and "overcharge" not in world.fired:
        world.fired.add("overcharge")
        relic.meters["glow"] = relic.meters.get("glow", 0.0) + 1
        out.append(f"The relic answered with a bright glow.")
    return out


def _r_happy_ending(world: World) -> list[str]:
    hero = world.entities["hero"]
    boss = world.entities["boss"]
    storm = world.entities["storm"]
    if hero.memes.get("hope", 0.0) >= THRESHOLD and hero.memes.get("courage", 0.0) >= THRESHOLD:
        if "peace" not in world.fired:
            world.fired.add("peace")
            boss.memes["soft"] = boss.memes.get("soft", 0.0) + 1
            storm.memes["calm"] = storm.memes.get("calm", 0.0) + 1
            return [f"The boss grew gentle, and the storm quieted to a purr."]
    return []


RULES = [Rule("overcharge", _r_overcharge), Rule("peace", _r_happy_ending)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


def tell(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id="hero", kind="character", type="apprentice", label=params.hero_name))
    boss = world.add(Entity(id="boss", kind="character", type="boss", label=params.boss_name))
    storm = world.add(Entity(id="storm", kind="character", type="storm", label=params.storm_name))
    relic = world.add(Entity(id="relic", kind="thing", type=params.relic, label=params.relic, phrase=f"an old {params.relic}"))

    world.facts.update(hero=hero, boss=boss, storm=storm, relic=relic)

    world.say(f"Long ago, in {PLACES[params.place]}, there lived a young helper named {hero.label}.")
    world.say(f"{hero.label} served under the boss {boss.label}, who watched the shrine and kept the lamps lit.")
    world.say(f"On the altar rested a {relic.label}, old as moonlight, said to answer only to a true and brave heart.")

    world.para()
    world.say(f"One night, the sky split with blue {params.place} voltage, and {storm.label} rumbled over the roof stones.")
    world.say(f"{hero.label} looked up and did not run. Instead, {hero.pronoun()} began to hypothesize the storm was not angry at all, but lonely.")
    world.say(f'That thought gave {hero.pronoun("object")} courage, and {hero.pronoun("possessive")} hands lifted the {relic.label} toward the lightning.')

    hero.meters["voltage"] = 1.0
    hero.memes["courage"] = 1.0
    hero.memes["hope"] = 1.0
    boss.memes["worry"] = 1.0

    propagate(world)

    world.para()
    world.say(f"The boss saw the brave guess, and instead of scolding, {boss.pronoun()} spoke kindly: "
              f'"If your hypothesis is true, then the storm only needs a friend."')
    world.say(f"{hero.label} sang to the wind, the {relic.label} shone like a small sun, and the storm bent low to listen.")
    propagate(world)

    world.para()
    world.say(f"At last the clouds opened wide, not to break the shrine, but to bless it with silver rain.")
    world.say(f"{storm.label} drifted away happy, {boss.label} smiled like dawn, and {hero.label} placed the glowing {relic.label} back on the altar.")
    world.say(f"So the village kept its light, the boss kept peace, and the brave little hypothesis became a happy ending.")

    world.facts["resolved"] = True
    world.facts["happy_ending"] = True
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    lines.append(asp.fact("theme", "voltage"))
    lines.append(asp.fact("theme", "boss"))
    lines.append(asp.fact("theme", "hypothesize"))
    lines.append(asp.fact("style", "myth"))
    lines.append(asp.fact("ending", "happy"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P) :- place(P), theme(voltage), theme(boss), theme(hypothesize), style(myth), ending(happy).
#show valid_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic voltage storyworld with a happy ending.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name")
    ap.add_argument("--boss")
    ap.add_argument("--storm")
    ap.add_argument("--relic", choices=RELICS)
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
    place = args.place or rng.choice(list(PLACES))
    name = args.name or rng.choice(HERO_NAMES)
    boss = args.boss or rng.choice(BOSS_NAMES)
    storm = args.storm or rng.choice(STORM_NAMES)
    relic = args.relic or rng.choice(RELICS)
    return StoryParams(place=place, hero_name=name, boss_name=boss, storm_name=storm, relic=relic)


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    hero, boss, storm, relic = p["hero"], p["boss"], p["storm"], p["relic"]
    return [
        f"Write a mythic children's story with voltage, a boss, and a happy ending.",
        f"Tell a short legend where {hero.label} serves {boss.label}, makes a bold hypothesize, and saves the {relic.label}.",
        f"Create a gentle myth about {storm.label}, bright voltage, and a clever guess that ends well.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    hero, boss, storm, relic = p["hero"], p["boss"], p["storm"], p["relic"]
    return [
        QAItem(
            question=f"Who made the brave hypothesize about the storm?",
            answer=f"{hero.label} did. {hero.label} guessed the storm was lonely instead of angry.",
        ),
        QAItem(
            question=f"Who was the boss in the shrine story?",
            answer=f"The boss was {boss.label}, who watched over the shrine and later spoke kindly.",
        ),
        QAItem(
            question=f"What object glowed when the voltage rose?",
            answer=f"The {relic.label} glowed when {hero.label} lifted it toward the lightning.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is voltage?",
            answer="Voltage is a kind of electric push that makes lightning and sparks feel powerful.",
        ),
        QAItem(
            question="What does it mean to hypothesize?",
            answer="To hypothesize means to make a thoughtful guess about why something is happening.",
        ),
        QAItem(
            question="What is a boss?",
            answer="A boss is a leader who gives directions or watches over a place or a job.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        if e.meters or e.memes:
            lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    import asp
    models = asp.solve(asp_program("#show valid_story/1."), models=1)
    if models:
        print("OK: ASP produced a valid mythic story shape.")
        return 0
    print("Mismatch: ASP produced no valid story.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="mountain", hero_name="Mira", boss_name="Boros", storm_name="Storm-King", relic="lantern"),
            StoryParams(place="valley", hero_name="Taro", boss_name="Kara", storm_name="Sky-Boss", relic="bell"),
            StoryParams(place="shore", hero_name="Lina", boss_name="Orun", storm_name="Thunder-Hound", relic="harp"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
