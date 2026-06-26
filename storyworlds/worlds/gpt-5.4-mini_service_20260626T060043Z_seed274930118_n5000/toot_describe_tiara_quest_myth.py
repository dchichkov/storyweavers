#!/usr/bin/env python3
"""
storyworlds/worlds/toot_describe_tiara_quest_myth.py
=====================================================

A small myth-flavored storyworld about a Quest, a toot, and a tiara.

Premise:
- A young quester carries a lost tiara through a moonlit land.
- A stone guardian will not open the gate unless the quester can toot a horn
  and describe the tiara clearly.
- The story turns on courage, memory, and a gentle return.

This world keeps the classical simulation shape from the Storyweavers contract:
entities have meters and memes, the prose is driven by state changes, and the
inline ASP twin mirrors the Python reasonableness gate.
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    label: str
    phrase: str
    risk: str
    region: str
    requires: set[str] = field(default_factory=set)
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    verb: str
    clears: set[str]
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_weight(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("burden", 0.0) >= THRESHOLD and ("weight", ent.id) not in world.fired:
            world.fired.add(("weight", ent.id))
            ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1
            out.append(f"{ent.label or ent.id} felt the burden grow heavier.")
    return out


def _r_bond(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.facts.get("seeker")
    tiara = world.facts.get("tiara")
    if seeker and tiara:
        s = world.get(seeker.id)
        t = world.get(tiara.id)
        if t.carried_by == s.id and s.memes.get("resolve", 0.0) >= THRESHOLD and ("bond", s.id) not in world.fired:
            world.fired.add(("bond", s.id))
            s.memes["hope"] = s.memes.get("hope", 0.0) + 1
            out.append("__bond__")
    return out


CAUSAL_RULES = [
    Rule("weight", _r_weight),
    Rule("bond", _r_bond),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                all_lines.extend([x for x in lines if x != "__bond__"])
    if narrate:
        for line in all_lines:
            world.say(line)
    return all_lines


def build_story_world(setting: Setting, hero_name: str, hero_type: str, mentor_type: str, relic: QuestItem, tool: Tool) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="the guide"))
    tiara = world.add(Entity(
        id="Tiara",
        type="tiara",
        label="tiara",
        phrase=relic.phrase,
        owner=hero.id,
        caretaker=mentor.id,
        carried_by=hero.id,
    ))
    horn = world.add(Entity(
        id=tool.id,
        type="horn",
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
    ))

    world.facts.update(seeker=hero, mentor=mentor, tiara=tiara, horn=horn, tool=tool, relic=relic)
    return world


def introduce(world: World) -> None:
    hero = world.facts["seeker"]
    world.say(
        f"{hero.id} was a young quester with a careful heart, and {hero.pronoun('possessive')} feet knew the old road well."
    )
    world.say(
        f"Every night, {hero.id} listened for legends about a lost {world.facts['relic'].label} and the gate that would only open for truth."
    )


def desire(world: World) -> None:
    hero = world.facts["seeker"]
    relic = world.facts["relic"]
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} wanted to finish the Quest and bring the {relic.label} home before the moon climbed high."
    )


def arrive_at_gate(world: World) -> None:
    hero = world.facts["seeker"]
    setting = world.setting
    world.say(
        f"One silver evening, {hero.id} reached {setting.place}, where the gate stood cold under {setting.sky} skies."
    )
    world.say("A stone guardian blinked once and waited for a sign.")


def ask_for_toot(world: World) -> None:
    hero = world.facts["seeker"]
    tool = world.facts["tool"]
    hero.meters["burden"] = hero.meters.get("burden", 0.0) + 1
    world.say(
        f"The guardian said, 'Toot the {tool.label}, and describe the {world.facts['relic'].label} so I know it is truly the lost one.'"
    )


def hesitate(world: World) -> None:
    hero = world.facts["seeker"]
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(
        f"{hero.id} held the {world.facts['tool'].label} close. The sound might wake the dark, and the words had to be exact."
    )


def mentor_gently(world: World) -> None:
    hero = world.facts["seeker"]
    mentor = world.facts["mentor"]
    world.say(
        f"{mentor.label} touched {hero.pronoun('possessive')} shoulder and said, 'A brave voice can be small and still be true.'"
    )


def perform_toot_and_describe(world: World) -> None:
    hero = world.facts["seeker"]
    tool = world.facts["tool"]
    relic = world.facts["relic"]
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    world.say(
        f"{hero.id} took a breath and gave a clear toot on the {tool.label}."
    )
    world.say(
        f"Then {hero.id} described the {relic.label}: its pale rim, the tiny star at the front, and the missing pearl at the side."
    )
    propagate(world, narrate=False)
    world.say(
        f"The guardian listened, nodded, and opened the gate."
    )


def resolve_story(world: World) -> None:
    hero = world.facts["seeker"]
    relic = world.facts["relic"]
    mentor = world.facts["mentor"]
    relic.carried_by = None
    relic.owner = "Queen"
    world.say(
        f"Beyond the gate, the queen received the {relic.label} with shining eyes."
    )
    world.say(
        f"{hero.id} had finished the Quest at last, and {mentor.label} smiled as the moonlit road grew soft behind {hero.pronoun('object')}."
    )


SETTINGS = {
    "moon_gate": Setting(place="the moon gate", sky="silver", affords={"quest"}),
    "hill_shrine": Setting(place="the hill shrine", sky="blue-black", affords={"quest"}),
    "river_arch": Setting(place="the river arch", sky="glowing", affords={"quest"}),
}

RELICS = {
    "star_tiara": QuestItem(
        label="tiara",
        phrase="a pale tiara with one tiny star and one missing pearl",
        risk="lost",
        region="head",
        requires={"toot", "describe"},
    ),
    "leaf_tiara": QuestItem(
        label="tiara",
        phrase="a green tiara braided with leaf shapes and soft silver thread",
        risk="hidden",
        region="head",
        requires={"toot", "describe"},
    ),
}

TOOLS = {
    "horn": Tool(
        id="Horn",
        label="horn",
        phrase="a small horn with a bright mouth",
        verb="toot",
        clears={"silence", "doubt"},
        covers={"voice"},
    ),
}

HERO_NAMES = ["Mira", "Orin", "Lia", "Tavi", "Sera", "Niko"]
HERO_TYPES = ["girl", "boy"]
MENTOR_TYPES = ["wizard", "priestess", "old guide", "queen"]


@dataclass
class StoryParams:
    place: str
    relic: str
    hero_name: str
    hero_type: str
    mentor_type: str
    seed: Optional[int] = None


def quest_valid(setting: Setting, relic: QuestItem) -> bool:
    return "quest" in setting.affords and "toot" in relic.requires and "describe" in relic.requires


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for relic_id, relic in RELICS.items():
            if quest_valid(setting, relic):
                combos.append((place, relic_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.relic and args.relic not in RELICS:
        raise StoryError("Unknown relic.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.relic is None or c[1] == args.relic)]
    if not combos:
        raise StoryError("(No valid quest fits those choices.)")
    place, relic_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    mentor_type = args.mentor_type or rng.choice(MENTOR_TYPES)
    return StoryParams(place=place, relic=relic_id, hero_name=hero_name, hero_type=hero_type, mentor_type=mentor_type)


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        'Write a short myth about a Quest, a toot, and a tiara.',
        f"Tell a child-friendly legend where {p['seeker'].id} must toot a horn and describe a tiara at {world.setting.place}.",
        f"Write a gentle myth in which a guardian opens a gate after hearing a toot and a careful description of the tiara.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    hero = p["seeker"]
    mentor = p["mentor"]
    relic = p["relic"]
    tool = p["tool"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to finish?",
            answer=f"{hero.id} was trying to finish a Quest and return the {relic.label} to its rightful home.",
        ),
        QAItem(
            question=f"What did the guardian ask {hero.id} to do before the gate would open?",
            answer=f"The guardian asked {hero.id} to toot the {tool.label} and describe the {relic.label} clearly.",
        ),
        QAItem(
            question=f"Who helped {hero.id} feel brave enough to speak?",
            answer=f"{mentor.label} helped by reminding {hero.id} that a small, true voice can still be brave.",
        ),
        QAItem(
            question=f"What happened after {hero.id} gave the toot and described the tiara?",
            answer=f"The guardian listened, opened the gate, and let {hero.id} continue the Quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tiara?",
            answer="A tiara is a light crown or headpiece, often worn like a sparkling band on the head.",
        ),
        QAItem(
            question="What does toot mean?",
            answer="Toot means to make a short sound on a horn or trumpet.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a long journey with a goal, like finding something lost or helping someone in need.",
        ),
        QAItem(
            question="Why does a guardian ask for a description?",
            answer="A guardian may ask for a description to make sure the right person or the right treasure has been found.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    relic = RELICS[params.relic]
    tool = TOOLS["horn"]
    world = build_story_world(setting, params.hero_name, params.hero_type, params.mentor_type, relic, tool)

    introduce(world)
    world.para()
    desire(world)
    arrive_at_gate(world)
    ask_for_toot(world)
    hesitate(world)
    mentor_gently(world)
    world.para()
    perform_toot_and_describe(world)
    resolve_story(world)
    world.facts["resolved"] = True
    return world


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


ASP_RULES = r"""
quest_valid(P, R) :- setting(P), relic(R), affords(P, quest), requires(R, toot), requires(R, describe).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for req in sorted(r.requires):
            lines.append(asp.fact("requires", rid, req))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_valid/2."))
    return sorted(set(asp.atoms(model, "quest_valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="moon_gate", relic="star_tiara", hero_name="Mira", hero_type="girl", mentor_type="wizard"),
    StoryParams(place="hill_shrine", relic="leaf_tiara", hero_name="Orin", hero_type="boy", mentor_type="old guide"),
    StoryParams(place="river_arch", relic="star_tiara", hero_name="Lia", hero_type="girl", mentor_type="priestess"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic quest world: toot, describe, tiara.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--mentor-type", choices=MENTOR_TYPES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid quest combos:\n")
        for place, relic in combos:
            print(f"  {place:12} {relic}")
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
            header = f"### {p.hero_name}: quest at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
