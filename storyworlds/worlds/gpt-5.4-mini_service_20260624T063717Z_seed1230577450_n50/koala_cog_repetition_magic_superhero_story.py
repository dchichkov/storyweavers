#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/koala_cog_repetition_magic_superhero_story.py
===============================================================================================================

A small superhero-style storyworld about a koala hero, a stubborn cog,
repetition, and a little bit of magic.

Premise:
- A koala hero patrols a tiny city workshop district.
- A magical cog keeps the district's rescue bell turning.
- Repetition is the hero's training power and also the source of the problem:
  the bell can only be made to ring when the hero repeats the right action
  three times.

Story shape:
- Beginning: the koala loves helping and carries a magic tool.
- Middle: the cog gets stuck; repeated tries do not help at first.
- Turn: the hero notices the pattern and uses repetition intentionally.
- Ending: the cog turns, the bell rings, and the hero saves the day.

This script is self-contained and follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- lazy ASP import for verification
- build_parser, resolve_params, generate, emit, main
- story, prompts, story QA, world QA, and trace support
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
    wearer: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"koala", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    repeated_verb: str
    trouble: str
    fix_hint: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    magical: bool = False


@dataclass
class Tool:
    id: str
    label: str
    power: str
    repeat_count: int
    works_on: set[str] = field(default_factory=set)
    magical: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.turns: int = 0
        self.repetition_done: int = 0
        self.cog_turns: int = 0

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.turns = self.turns
        clone.repetition_done = self.repetition_done
        clone.cog_turns = self.cog_turns
        return clone


def _meter(entity: Entity, key: str, delta: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + delta


def _mem(entity: Entity, key: str, delta: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + delta


SETTINGS = {
    "workshop": Setting(
        place="the clockwork workshop",
        detail="Brass beams hummed above the benches, and a tiny rescue bell hung by the door.",
        affords={"repair", "practice", "rescue"},
    ),
    "rooftop": Setting(
        place="the rooftop garden",
        detail="The rooftop looked over the city, with moonflowers beside a small signal lamp.",
        affords={"repair", "practice", "rescue"},
    ),
}

CHALLENGES = {
    "stuck_cog": Challenge(
        id="stuck_cog",
        verb="free the cog",
        repeated_verb="tap the cog again and again",
        trouble="stuck tight",
        fix_hint="use the same careful tap three times",
        keyword="cog",
        tags={"cog", "repeat"},
    ),
    "silent_bell": Challenge(
        id="silent_bell",
        verb="wake the bell",
        repeated_verb="ring the bell again and again",
        trouble="silent",
        fix_hint="repeat the magic chime three times",
        keyword="bell",
        tags={"magic", "repeat"},
    ),
}

RELICS = {
    "cog": Relic(
        id="cog",
        label="cog",
        phrase="a bright brass cog with a tiny star mark",
        region="hand",
        magical=True,
    ),
    "bell": Relic(
        id="bell",
        label="bell",
        phrase="a small rescue bell",
        region="air",
        magical=True,
    ),
}

TOOLS = {
    "glow_tap": Tool(
        id="glow_tap",
        label="a glowing tapper",
        power="make little sparks",
        repeat_count=3,
        works_on={"cog", "bell"},
        magical=True,
    ),
    "echo_gesture": Tool(
        id="echo_gesture",
        label="a mirror glove",
        power="repeat a motion exactly",
        repeat_count=3,
        works_on={"cog"},
        magical=True,
    ),
}

HERO_NAMES = ["Kira", "Niko", "Milo", "Ruby", "Tess", "Arlo"]
HERO_TRAITS = ["brave", "kind", "curious", "steady", "bright"]
SIDEKICK_NAMES = ["Pip", "Juno", "Bea", "Ollie"]


@dataclass
class StoryParams:
    setting: str
    challenge: str
    relic: str
    name: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: koala, cog, repetition, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICK_NAMES)
    ap.add_argument("--trait", choices=HERO_TRAITS)
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


def prize_at_risk(challenge: Challenge, relic: Relic) -> bool:
    if challenge.id == "stuck_cog":
        return relic.id == "cog"
    if challenge.id == "silent_bell":
        return relic.id == "bell"
    return False


def compatible_fix(challenge: Challenge, relic: Relic) -> Optional[Tool]:
    for tool in TOOLS.values():
        if relic.id in tool.works_on and tool.repeat_count == 3 and tool.magical:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting in SETTINGS:
        for challenge_id, challenge in CHALLENGES.items():
            for relic_id, relic in RELICS.items():
                if prize_at_risk(challenge, relic) and compatible_fix(challenge, relic):
                    out.append((setting, challenge_id, relic_id))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.relic:
        if not prize_at_risk(CHALLENGES[args.challenge], RELICS[args.relic]):
            raise StoryError("No story: that challenge does not actually threaten that relic.")
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.relic is None or c[2] == args.relic)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, challenge_id, relic_id = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        challenge=challenge_id,
        relic=relic_id,
        name=args.name or rng.choice(HERO_NAMES),
        sidekick=args.sidekick or rng.choice(SIDEKICK_NAMES),
        trait=args.trait or rng.choice(HERO_TRAITS),
    )


def _do_repetition(world: World, hero: Entity, tool: Tool, challenge: Challenge, narrate: bool = True) -> None:
    _mem(hero, "focus", 1.0)
    world.repetition_done += 1
    if narrate:
        world.say(f"{hero.id} used the {tool.label} to {challenge.repeated_verb}.")
    if world.repetition_done >= tool.repeat_count:
        if challenge.id == "stuck_cog":
            cog = world.get("cog")
            _meter(cog, "stuck", -1.0)
            _meter(cog, "turns", 1.0)
            world.cog_turns += 1
        elif challenge.id == "silent_bell":
            bell = world.get("bell")
            _meter(bell, "silent", -1.0)
            _meter(bell, "ring", 1.0)


def predict(world: World, challenge: Challenge, tool: Tool) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    for _ in range(tool.repeat_count):
        _do_repetition(sim, hero, tool, challenge, narrate=False)
    if challenge.id == "stuck_cog":
        return {"fixed": sim.get("cog").meters.get("stuck", 0.0) < THRESHOLD}
    return {"fixed": sim.get("bell").meters.get("silent", 0.0) < THRESHOLD}


def tell(setting: Setting, challenge: Challenge, relic: Relic, name: str, sidekick: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="koala", label="koala hero", traits=[trait, "heroic"]))
    friend = world.add(Entity(id=sidekick, kind="character", type="sidekick", label="small helper", traits=["helpful"]))
    cog = world.add(Entity(id="cog", type="cog", label="cog", phrase=RELICS["cog"].phrase, owner=hero.id))
    bell = world.add(Entity(id="bell", type="bell", label="bell", phrase=RELICS["bell"].phrase))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS["glow_tap"].label, phrase=TOOLS["glow_tap"].label))
    world.facts.update(hero=hero, friend=friend, challenge=challenge, relic=relic, tool=TOOLS["glow_tap"])
    world.say(f"{hero.id} was a {trait} koala hero who watched over {setting.place}.")
    world.say(f"He carried {TOOLS['glow_tap'].label}, a little magic tool that could {TOOLS['glow_tap'].power}.")
    world.say(f"Nearby, {relic.phrase if relic.id == 'cog' else RELICS['cog'].phrase} waited beside {setting.detail.lower()}")
    world.para()
    world.say(f"One day, {relic.label if relic.id == 'cog' else 'the cog'} got {challenge.trouble}.")
    world.say(f"{hero.id} tried to {challenge.verb}, but one try was not enough.")
    world.say(f"{sidekick} whispered, 'Maybe the hero needs a repeating trick.'")
    world.para()
    for i in range(3):
        _do_repetition(world, hero, TOOLS["glow_tap"], challenge, narrate=True)
        if i == 0:
            world.say(f"Nothing changed yet, so {hero.id} tried again.")
        elif i == 1:
            world.say(f"The magic still needed one more careful repeat.")
    world.say(f"On the third try, the {relic.label} turned, and the rescue bell shone.")
    world.say(f"{hero.id} smiled as the city heard the new ring, and {sidekick} cheered.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story for a young child about a koala hero, a {f['challenge'].keyword}, and a magic tool.",
        f"Tell a gentle action story where {f['hero'].id} must repeat a brave move three times to fix a stuck {f['relic'].label}.",
        "Write a short magical rescue story with a koala hero, a cog, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    challenge = f["challenge"]
    relic = f["relic"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who is the hero in the story?",
            answer=f"The hero is {hero.id}, a brave koala who watches over {world.setting.place}.",
        ),
        QAItem(
            question=f"What problem did {relic.label} have?",
            answer=f"The {relic.label} got {challenge.trouble}, so it would not help the rescue bell at first.",
        ),
        QAItem(
            question=f"What did {hero.id} keep doing to solve the problem?",
            answer=f"{hero.id} kept repeating the same careful action with {tool.label} three times.",
        ),
        QAItem(
            question=f"Who encouraged the hero to try a repeating trick?",
            answer=f"{friend.id} did. {friend.id} reminded the hero that a repeating trick might help.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The {relic.label} turned, the rescue bell shone, and the city got help.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a cog?",
            answer="A cog is a toothed wheel that helps machines turn and move together.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing the same action again and again.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special that can do impossible things, like making tiny sparks or helping a tool work.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("region", rid, r.region))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("repeat_count", tid, t.repeat_count))
        if t.magical:
            lines.append(asp.fact("magical", tid))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(C, R) :- challenge(C), relic(R), risk_pair(C, R).
compatible_fix(C, T) :- challenge(C), tool(T), needs_repeat(C), repeat_count(T, 3), magical(T), usable_on(T, C).
valid_story(S, C, R) :- setting(S), prize_at_risk(C, R), has_fix(C, R).
has_fix(C, R) :- prize_at_risk(C, R), compatible(C, R).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - asp_set))
    print("asp only:", sorted(asp_set - py))
    return 1


def resolve_params_stub(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHALLENGES[params.challenge], RELICS[params.relic], params.name, params.sidekick, params.trait)
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="workshop", challenge="stuck_cog", relic="cog", name="Kira", sidekick="Pip", trait="brave"),
    StoryParams(setting="rooftop", challenge="silent_bell", relic="bell", name="Milo", sidekick="Juno", trait="steady"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.relic and not prize_at_risk(CHALLENGES[args.challenge], RELICS[args.relic]):
        raise StoryError("No story: that challenge does not actually threaten that relic.")
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting) and (args.challenge is None or c[1] == args.challenge) and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, challenge, relic = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        challenge=challenge,
        relic=relic,
        name=args.name or rng.choice(HERO_NAMES),
        sidekick=args.sidekick or rng.choice(SIDEKICK_NAMES),
        trait=args.trait or rng.choice(HERO_TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
