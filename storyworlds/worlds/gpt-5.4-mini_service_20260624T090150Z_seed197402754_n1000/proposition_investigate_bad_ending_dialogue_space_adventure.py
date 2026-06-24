#!/usr/bin/env python3
"""
storyworlds/worlds/proposition_investigate_bad_ending_dialogue_space_adventure.py
=================================================================================

A small space-adventure storyworld about a crew, a proposition, an investigation,
and a bad ending reached through dialogue and evidence.

Seed idea:
---
A child astronaut and a small robot hear a strange signal while traveling through
space. Someone makes a hopeful proposition: maybe the signal means there is a
friendly rescue ship, or a safe planet, or a treasure cache. They investigate,
talk it through, and discover the signal means something else. The ending is bad:
the crew misses a safe chance, loses time or fuel, and must drift away with the
wrong hope.

This world keeps the premise tiny and classical:
- one proposition to test,
- one investigation that gathers evidence,
- one dialogue beat that changes the choice,
- one bad ending image proving what changed.

The generated prose is state-driven rather than a fixed template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    kind: str  # "ship" | "moon" | "station" | "asteroid"
    ambience: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Proposition:
    id: str
    claim: str
    hope: str
    question: str
    evidence_needed: str
    bad_result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class InvestigationTool:
    id: str
    label: str
    verb: str
    yields: str
    reveals: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        other = World(self.setting)
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


def name_phrase(name: str, role: str) -> str:
    return f"{name}, the {role}"


def investigate(world: World, crew: Entity, prop: Proposition, tool: InvestigationTool) -> None:
    crew.memes["curiosity"] = crew.memes.get("curiosity", 0) + 1
    world.say(
        f"{crew.id} wanted to investigate the idea that {prop.claim}. "
        f"{crew.pronoun().capitalize()} took the {tool.label} and listened for clues."
    )
    world.say(
        f"The {tool.label} found {tool.yields}, and that revealed {tool.reveals}."
    )


def dialogue(world: World, crew: Entity, partner: Entity, prop: Proposition, tool: InvestigationTool) -> None:
    crew.memes["worry"] = crew.memes.get("worry", 0) + 1
    partner.memes["worry"] = partner.memes.get("worry", 0) + 1
    world.say(
        f'"Could it still be true?" {crew.id} asked. "{prop.claim}?"'
    )
    world.say(
        f'"I hoped so," {partner.id} said, "but the {tool.label} shows {prop.bad_result}."'
    )


def bad_ending(world: World, crew: Entity, partner: Entity, prop: Proposition) -> None:
    crew.memes["sadness"] = crew.memes.get("sadness", 0) + 1
    partner.memes["sadness"] = partner.memes.get("sadness", 0) + 1
    world.say(
        f"They had to admit the {prop.claim.split(' ', 1)[0]} was wrong."
    )
    world.say(
        f"The ship drifted on while {prop.bad_result}, and {crew.id} stared at the dim window."
    )


def setup_world(setting: Setting, prop: Proposition, tool: InvestigationTool,
                name: str, partner_name: str, crew_type: str, partner_type: str) -> World:
    world = World(setting)
    crew = world.add(Entity(id=name, kind="character", type=crew_type))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type))
    tool_ent = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label,
                                owner=crew.id, carried_by=crew.id))
    beacon = world.add(Entity(id=prop.id, kind="thing", type="signal", label=prop.id))
    world.facts.update(
        crew=crew, partner=partner, tool=tool_ent, proposition=prop, setting=setting,
    )
    world.say(
        f"{name_phrase(crew.id, crew.type)} floated through {setting.place}, "
        f"where the air was {setting.ambience}."
    )
    world.say(
        f"Then a new proposition came over the radio: {prop.claim}."
    )
    return world


def tell(setting: Setting, prop: Proposition, tool: InvestigationTool,
         name: str = "Mira", partner_name: str = "Pip",
         crew_type: str = "girl", partner_type: str = "robot") -> World:
    world = setup_world(setting, prop, tool, name, partner_name, crew_type, partner_type)
    crew = world.get(name)
    partner = world.get(partner_name)

    world.para()
    world.say(
        f"{crew.id} liked the hopeful part of it: {prop.hope}."
    )
    world.say(
        f"{partner.id} blinked and said, \"Let's investigate before we chase it.\""
    )

    world.para()
    investigate(world, crew, prop, tool)
    dialogue(world, crew, partner, prop, tool)

    world.para()
    bad_ending(world, crew, partner, prop)
    world.say(
        f"In the end, the {tool.label} stayed warm in {crew.id}'s hand, and the dark window showed only empty space."
    )

    world.facts["resolved"] = False
    world.facts["bad_ending"] = True
    return world


SETTINGS = {
    "moon_base": Setting(
        place="Moon Base Blue",
        kind="station",
        ambience="cool and quiet",
        affords={"radio", "scan"},
    ),
    "starship": Setting(
        place="the little starship",
        kind="ship",
        ambience="bright with blinking panels",
        affords={"radio", "scan"},
    ),
    "orbit_station": Setting(
        place="the orbit station",
        kind="station",
        ambience="soft and humming",
        affords={"radio", "scan"},
    ),
}

PROPOSITIONS = {
    "rescue": Proposition(
        id="rescue_signal",
        claim="the signal means a rescue ship is nearby",
        hope="they could go home soon",
        question="What does the strange signal mean?",
        evidence_needed="a clear rescue beacon",
        bad_result="it was only an old alarm ping from a broken buoy",
        tags={"signal", "rescue", "radio"},
    ),
    "planet": Proposition(
        id="safe_planet",
        claim="there is a safe planet below the clouds",
        hope="they could land and rest on solid ground",
        question="Is there a safe place to land?",
        evidence_needed="a landing map and a calm sky scan",
        bad_result="the clouds hide a stormy, rocky world with no safe landing spot",
        tags={"planet", "storm", "scan"},
    ),
    "treasure": Proposition(
        id="lost_treasure",
        claim="the faint echo points to lost treasure in the asteroid",
        hope="they could bring back something shiny and special",
        question="Is the echo hiding treasure?",
        evidence_needed="a strong metal reading",
        bad_result="the echo came from a cracked fuel pipe inside the rock",
        tags={"asteroid", "echo", "treasure"},
    ),
}

TOOLS = {
    "scanner": InvestigationTool(
        id="scanner",
        label="scanner",
        verb="scan",
        yields="a faint map of the waves",
        reveals="the signal was coming from the wrong place",
        guards={"signal", "scan"},
    ),
    "radio_tuner": InvestigationTool(
        id="radio_tuner",
        label="radio tuner",
        verb="tune the radio",
        yields="a squeal and a wobble in the message",
        reveals="the message repeated an old broken loop",
        guards={"radio", "signal"},
    ),
    "metal_probe": InvestigationTool(
        id="metal_probe",
        label="metal probe",
        verb="tap the rock",
        yields="a sharp hollow echo",
        reveals="the sound bounced off an empty pipe instead of treasure",
        guards={"asteroid", "echo"},
    ),
}

NAMES = ["Mira", "Nico", "Ari", "Juno", "Luna", "Nova", "Kai", "Zuri"]
PARTNERS = ["Pip", "Tiko", "Byte", "Roo", "Bex"]
CREW_TYPES = ["girl", "boy"]
PARTNER_TYPES = ["robot"]


@dataclass
class StoryParams:
    setting: str
    proposition: str
    tool: str
    name: str
    partner_name: str
    crew_type: str
    partner_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid, prop in PROPOSITIONS.items():
            if not setting.affords:
                continue
            for tid, tool in TOOLS.items():
                if prop.tags & tool.guards:
                    combos.append((sid, pid, tid))
    return combos


def explain_rejection(setting_id: str, prop_id: str, tool_id: str) -> str:
    prop = PROPOSITIONS[prop_id]
    tool = TOOLS[tool_id]
    return (
        f"(No story: the {tool.label} does not give useful evidence for "
        f"'{prop.claim}'. Try a different investigation tool.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.proposition is None or c[1] == args.proposition)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid space-adventure combination matches the given options.)")
    sid, pid, tid = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    partner_name = args.partner_name or rng.choice(PARTNERS)
    crew_type = args.crew_type or rng.choice(CREW_TYPES)
    partner_type = args.partner_type or "robot"
    return StoryParams(
        setting=sid,
        proposition=pid,
        tool=tid,
        name=name,
        partner_name=partner_name,
        crew_type=crew_type,
        partner_type=partner_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prop: Proposition = f["proposition"]
    tool: InvestigationTool = f["tool"]
    setting: Setting = f["setting"]
    crew: Entity = f["crew"]
    return [
        f'Write a short space adventure story for a child where someone says, "{prop.claim}", and the crew decides to investigate.',
        f"Tell a dialogue-rich story set in {setting.place} where {crew.id} uses a {tool.label} to test the proposition that {prop.claim}.",
        f'Write a gentle but sad ending story that includes the word "investigate" and ends with a bad result from space.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    prop: Proposition = f["proposition"]
    tool: InvestigationTool = f["tool"]
    crew: Entity = f["crew"]
    partner: Entity = f["partner"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What proposition did {crew.id} want to investigate in {setting.place}?",
            answer=f"{crew.id} wanted to investigate whether {prop.claim}.",
        ),
        QAItem(
            question=f"Who talked with {crew.id} during the investigation?",
            answer=f"{partner.id}, the robot, talked with {crew.id} and helped look at the clues.",
        ),
        QAItem(
            question=f"What tool did {crew.id} use to investigate the idea?",
            answer=f"{crew.id} used the {tool.label} to gather evidence.",
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer=f"It ended badly because the evidence showed that {prop.bad_result}, so the hopeful idea was wrong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does investigate mean?",
            answer="To investigate means to look closely for clues so you can learn what is really happening.",
        ),
        QAItem(
            question="What is a proposition?",
            answer="A proposition is an idea or claim that someone thinks might be true and wants to test.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things do not work out well for the characters, even after they try hard.",
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("starship", "rescue", "radio_tuner", "Mira", "Pip", "girl", "robot"),
    StoryParams("moon_base", "planet", "scanner", "Nico", "Byte", "boy", "robot"),
    StoryParams("orbit_station", "treasure", "metal_probe", "Ari", "Roo", "girl", "robot"),
]


ASP_RULES = r"""
% A proposition becomes investigable when the setting affords the needed kind of evidence.
can_investigate(S, P, T) :- setting(S), proposition(P), tool(T),
    prop_tag(P, Tag), tool_guard(T, Tag).

% If the right tool is used, evidence is revealed.
has_evidence(P, T) :- proposition(P), tool(T), prop_tag(P, Tag), tool_guard(T, Tag).

% A bad ending happens when the evidence disproves the proposition.
bad_ending(S, P, T) :- can_investigate(S, P, T), has_evidence(P, T).

#show can_investigate/3.
#show has_evidence/2.
#show bad_ending/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROPOSITIONS.items():
        lines.append(asp.fact("proposition", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("prop_tag", pid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("tool_guard", tid, g))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_set = set(asp.atoms(model, "bad_ending"))
    py_set = {(s, p, t) for s, p, t in valid_combos()}
    if asp_set != py_set:
        print("MISMATCH between ASP and python gates:")
        print("  only in ASP:", sorted(asp_set - py_set))
        print("  only in python:", sorted(py_set - asp_set))
        return 1
    print(f"OK: ASP matches python valid_combos() ({len(py_set)} combos).")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PROPOSITIONS[params.proposition],
        TOOLS[params.tool],
        params.name,
        params.partner_name,
        params.crew_type,
        params.partner_type,
    )
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about a proposition, an investigation, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--proposition", choices=PROPOSITIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--partner-name")
    ap.add_argument("--crew-type", choices=CREW_TYPES)
    ap.add_argument("--partner-type", choices=PARTNER_TYPES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(asp.atoms(model, 'bad_ending'))} compatible story combos:")
        for sid, pid, tid in valid_combos():
            print(f"  {sid:12} {pid:12} {tid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(setting=sid, proposition=pid, tool=tid,
                                 name="Mira", partner_name="Pip",
                                 crew_type="girl", partner_type="robot"))
            for sid, pid, tid in CURATED
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.proposition} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
