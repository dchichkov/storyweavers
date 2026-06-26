#!/usr/bin/env python3
"""
storyworlds/worlds/reign_spike_dim_bravery_space_adventure.py
=============================================================

A small classical story world for a space-adventure tale about bravery, a
narrow spike-dim passage, and a fragile reign that must be protected.

The source premise:
- A young space ruler wants to keep a quiet reign over a tiny moon-harbor.
- A dangerous spike-dim rift opens in the starway and threatens the route.
- The brave hero must choose whether to hide, panic, or guide the crew through.
- With a careful tool, a steady helper, and bravery, the group reaches safety
  and the reign becomes stronger instead of brittle.

This script models:
- physical meters: distance, damage, drift, light, shield, noise
- emotional memes: bravery, fear, trust, relief, pride, strain

It includes:
- a Python reasonableness gate
- an inline ASP twin
- generation, text/JSON emission, QA, and verify support
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "captain"}
        male = {"boy", "man", "king", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    starway: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    danger: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    blocks: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "moon_harbor": Setting(
        place="the moon harbor",
        starway="the silver starway",
        affords={"navigate", "scan"},
    ),
    "orbital_garden": Setting(
        place="the orbital garden",
        starway="the bright starway",
        affords={"navigate", "scan"},
    ),
}

CHALLENGES = {
    "spike_dim": Challenge(
        id="spike_dim",
        verb="guide the ship through the spike-dim rift",
        gerund="guiding the ship through the spike-dim rift",
        rush="dash toward the rift",
        hazard="the spike-dim rift could scrape the hull",
        danger="spike-dim damage",
        zone={"hull", "bridge"},
        keyword="spike-dim",
        tags={"spike-dim", "rift", "space"},
    ),
    "meteor_lane": Challenge(
        id="meteor_lane",
        verb="cross the meteor lane",
        gerund="crossing the meteor lane",
        rush="hurry into the lane",
        hazard="the meteors could crack the hull",
        danger="meteor damage",
        zone={"hull"},
        keyword="meteor",
        tags={"space", "meteors"},
    ),
}

PRIZES = {
    "reign": Prize(
        id="reign",
        label="reign",
        phrase="a calm reign over the moon harbor",
        region="bridge",
    ),
    "signal": Prize(
        id="signal",
        label="signal lamp",
        phrase="a bright signal lamp",
        region="bridge",
    ),
}

TOOLS = {
    "shield": Tool(
        id="shield",
        label="a spike-dim shield",
        covers={"hull", "bridge"},
        blocks={"spike-dim"},
        prep="switch on the spike-dim shield",
        tail="switched on the spike-dim shield",
    ),
    "helm": Tool(
        id="helm",
        label="a steady helm brace",
        covers={"bridge"},
        blocks={"meteor"},
        prep="lock in the steady helm brace",
        tail="locked in the steady helm brace",
    ),
}

HEROES = {
    "brave_ira": ("Ira", "girl"),
    "brave_jon": ("Jon", "boy"),
    "brave_nova": ("Nova", "girl"),
    "brave_ren": ("Ren", "boy"),
}

HELPERS = ["navigator", "engineer", "pilot"]
TRAITS = ["brave", "steady", "quick-thinking", "curious"]


@dataclass
class StoryParams:
    setting: str
    challenge: str
    prize: str
    hero_name: str
    hero_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


def _story_reasonable(setting: Setting, challenge: Challenge, prize: Prize) -> bool:
    if challenge.id == "spike_dim" and prize.id == "reign":
        return True
    if challenge.id == "meteor_lane" and prize.id == "signal":
        return True
    return False


def _select_tool(challenge: Challenge, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS.values():
        if challenge.keyword in tool.blocks and prize.region in tool.covers:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, s in SETTINGS.items():
        for c_id, c in CHALLENGES.items():
            for p_id, p in PRIZES.items():
                if _story_reasonable(s, c, p) and _select_tool(c, p):
                    out.append((s_id, c_id, p_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world about bravery and a spike-dim rift.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.prize:
        if not _story_reasonable(SETTINGS[args.setting] if args.setting else list(SETTINGS.values())[0],
                                 CHALLENGES[args.challenge], PRIZES[args.prize]):
            raise StoryError("No honest story: that challenge does not threaten that prize.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    s_id, c_id, p_id = rng.choice(sorted(combos))
    hero_name, hero_type = HEROES[rng.choice(list(HEROES))]
    return StoryParams(
        setting=s_id,
        challenge=c_id,
        prize=p_id,
        hero_name=args.name or hero_name,
        hero_type=hero_type,
        helper=args.helper or rng.choice(HELPERS),
        trait=args.trait or rng.choice(TRAITS),
    )


def _do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    world.zone = set(challenge.zone)
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.meters["risk"] = hero.meters.get("risk", 0.0) + 1
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} moved toward the {challenge.keyword} rift with steady bravery.")
    for ent in world.entities.values():
        if ent.kind == "thing" and ent.carried_by == hero.id and challenge.keyword in world.facts.get("tool_blocks", set()):
            ent.meters["damage"] = ent.meters.get("damage", 0.0) + 1


def predict_damage(world: World, hero: Entity, challenge: Challenge, prize_id: str) -> bool:
    sim = world.copy()
    _do_challenge(sim, sim.get(hero.id), challenge, narrate=False)
    return bool(sim.get(prize_id).meters.get("damage", 0.0) >= THRESHOLD)


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize,
         hero_name: str, hero_type: str, helper: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"bravery": 0.0, "fear": 0.0, "trust": 0.0}))
    helper_ent = world.add(Entity(id=helper, kind="character", type="pilot", meters={}, memes={"trust": 0.0}))
    prize = world.add(Entity(id=prize_cfg.id, type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=helper_ent.id, meters={}, memes={}))
    tool_def = _select_tool(challenge, prize_cfg)
    tool = world.add(Entity(id=tool_def.id, type="thing", label=tool_def.label, owner=hero.id, carried_by=hero.id, meters={}, memes={}))
    world.facts.update(hero=hero, helper=helper_ent, prize=prize, challenge=challenge, tool_def=tool_def, tool_blocks=set(tool_def.blocks), setting=setting)

    world.say(f"{hero_name} was a {trait} young space ruler whose {prize.label} symbolized a tiny but important reign over {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} liked calm maps, blinking panels, and the long silver starway that led past the harbor lights.")
    world.say(f"One day, a {challenge.keyword} rift opened ahead, and {challenge.hazard}.")
    world.para()
    world.say(f"{hero_name} and the {helper} went to {setting.place} to {challenge.verb}.")
    world.say(f"{hero_name} wanted to act fast, but {hero.pronoun('possessive')} heart beat hard because the route felt narrow and sharp.")
    if predict_damage(world, hero, challenge, prize_cfg.id):
        hero.memes["fear"] += 1
        world.say(f'"If we go in too quickly, {prize.label} could be ruined," said the {helper}.')
    world.para()
    if tool_def:
        world.say(f"{hero_name} took a deep breath, and {hero.pronoun('possessive')} bravery got louder than the fear.")
        world.say(f'"Let\'s {tool_def.prep}," {hero_name} said.')
        if challenge.keyword == "spike-dim":
            world.say(f"{hero_name} turned the ship toward the rift, but the shield held the sharp edges away.")
        else:
            world.say(f"{hero_name} steadied the ship, and the brace kept the bridge from shaking.")
        hero.memes["bravery"] += 1
        hero.memes["trust"] += 1
        helper_ent.memes["trust"] += 1
        prize.meters["damage"] = 0.0
        world.say(f"At the center of the crossing, {hero_name} kept {prize.label} safe, and the crew crossed in a bright hush.")
        world.say(f"When they came out, {hero_name}'s reign felt stronger, because {hero_name} had been brave for everyone.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a child about bravery, a {f["challenge"].keyword} rift, and a ruler named {f["hero"].id}.',
        f"Tell a gentle story where {f['hero'].id} must protect {f['prize'].label} during a dangerous starway crossing.",
        f'Write a simple story that uses the word "{f["challenge"].keyword}" and ends with a calm reign after a risky flight.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    helper = f["helper"]
    challenge = f["challenge"]
    tool_def = f["tool_def"]
    return [
        QAItem(
            question=f"Who was the story about in the moon harbor?",
            answer=f"It was about {hero.id}, a {hero.type} ruler who cared about {prize.label} and wanted to keep a calm reign.",
        ),
        QAItem(
            question=f"What danger made the crossing hard?",
            answer=f"A {challenge.keyword} rift opened in the starway, and {challenge.hazard}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the crossing?",
            answer=f"The {helper} helped by staying close, watching the route, and keeping the ship steady.",
        ),
        QAItem(
            question=f"What tool made the brave plan work?",
            answer=f"{tool_def.label} helped because it protected the ship from the {challenge.keyword} danger while {hero.id} crossed.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and relieved, because bravery helped keep the prize safe and the reign steady.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels afraid but still chooses to do what is needed or right.",
        ),
        QAItem(
            question="What is a rift in space?",
            answer="A rift in space is a dangerous opening or crack that can make travel hard and risky.",
        ),
        QAItem(
            question="Why do ships use shields?",
            answer="Ships use shields to protect themselves from danger, like sharp debris or strange energy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHALLENGES[params.challenge], PRIZES[params.prize],
                 params.hero_name, params.hero_type, params.helper, params.trait)
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
prize_at_risk(C, P) :- danger(C, K), prize_kind(P, K).
has_fix(C, P) :- prize_at_risk(C, P), tool_blocks(T, K), danger(C, K), tool_covers(T, R), prize_region(P, R).
valid_story(S, C, P) :- setting(S), challenge(C), prize(P), affords(S, C), prize_at_risk(C, P), has_fix(C, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("danger", cid, c.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_kind", pid, pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for b in sorted(t.blocks):
            lines.append(asp.fact("tool_blocks", tid, b))
        for c in sorted(t.covers):
            lines.append(asp.fact("tool_covers", tid, c))
    return "\n".join(lines)


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
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(py - asp_set))
    print("clingo only:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams("moon_harbor", "spike_dim", "reign", "Ira", "girl", "navigator", "brave"),
    StoryParams("orbital_garden", "meteor_lane", "signal", "Nova", "girl", "engineer", "steady"),
]


def resolve_gender(name: str) -> str:
    return "girl" if name in {"Ira", "Nova"} else "boy"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
