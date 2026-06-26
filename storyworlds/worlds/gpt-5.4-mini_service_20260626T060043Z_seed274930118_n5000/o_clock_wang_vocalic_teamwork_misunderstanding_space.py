#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure domain.

Premise:
- A crew is on a little mission at a clockwork space station.
- A strange "wang" sound and a "vocalic" signal create a misunderstanding.
- Teamwork resolves the problem and gets the crew home on time.

The world is intentionally tiny and constraint-checked:
- The mission only makes sense when the signal can be misunderstood.
- A valid fix requires teamwork plus a tool that can decode the signal.
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


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    station_name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    misunderstanding: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SETTINGS = {
    "hangar": Setting(place="the hangar", station_name="Clockfall Station", affords={"listen", "repair", "signal"}),
    "airlock": Setting(place="the airlock", station_name="Clockfall Station", affords={"listen", "repair", "signal"}),
    "observation": Setting(place="the observation deck", station_name="Clockfall Station", affords={"listen", "repair", "signal"}),
}

ACTIVITIES = {
    "listen": Activity(
        id="listen",
        verb="listen for the docking tone",
        gerund="listening for the docking tone",
        rush="run toward the comm panel",
        noise="wang",
        misunderstanding="the crew thought the wang meant a broken wheel",
        keyword="o'clock",
        tags={"wang", "o'clock"},
    ),
    "signal": Activity(
        id="signal",
        verb="send the beacon signal",
        gerund="sending the beacon signal",
        rush="tap the beacon keys too fast",
        noise="vocalic",
        misunderstanding="the crew thought the vocalic chirp meant the beacon was failing",
        keyword="vocalic",
        tags={"vocalic", "signal"},
    ),
    "repair": Activity(
        id="repair",
        verb="repair the little antenna",
        gerund="repairing the little antenna",
        rush="grab the tool kit and hurry",
        noise="wang",
        misunderstanding="the crew thought the wang came from a loose bolt",
        keyword="wang",
        tags={"wang", "repair"},
    ),
}

TOOLS = {
    "decoder": Tool(
        id="decoder",
        label="a vowel decoder",
        phrase="a tiny vowel decoder",
        prep="plug in the vowel decoder first",
        tail="plugged in the vowel decoder",
        guards={"vocalic", "wang"},
        covers={"comm"},
    ),
    "timer": Tool(
        id="timer",
        label="a round ship timer",
        phrase="a round ship timer marked o'clock",
        prep="check the ship timer first",
        tail="checked the ship timer",
        guards={"o'clock"},
        covers={"bridge"},
    ),
    "headset": Tool(
        id="headset",
        label="a teamwork headset",
        phrase="matching teamwork headsets",
        prep="put on the teamwork headsets",
        tail="put on the teamwork headsets",
        guards={"wang", "vocalic", "o'clock"},
        covers={"comm", "bridge"},
    ),
}

CREW_NAMES = ["Ari", "Mira", "Jun", "Pip", "Rae", "Tess"]
CREW_TYPES = ["girl", "boy", "captain", "pilot"]
TRAITS = ["brave", "curious", "patient", "quick", "careful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    crew_name: str
    crew_type: str
    partner_name: str
    partner_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% An activity is confusing when its signal matches a hearable cue.
confusing(A) :- activity(A), hears(A, N), odd_sound(N).

% A useful tool solves confusion only if it guards the signal and covers the room.
fix(A, T) :- confusing(A), tool(T), handles(T, N), hears(A, N), covers(T, R), room(A, R).

valid(P, A, T) :- setting(P), affords(P, A), activity(A), confusing(A), fix(A, T).
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
        lines.append(asp.fact("hears", aid, a.noise))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("handles", tid, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
    for n in ["wang", "vocalic", "o'clock"]:
        lines.append(asp.fact("odd_sound", n))
    for p, s in SETTINGS.items():
        for a in sorted(s.affords):
            lines.append(asp.fact("room", a, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(setting: Setting, activity: Activity) -> None:
    if activity.id not in setting.affords:
        raise StoryError("That activity cannot happen in that setting.")
    if "wang" not in activity.tags and "vocalic" not in activity.tags and "o'clock" not in activity.tags:
        raise StoryError("This world needs a wang, vocalic, or o'clock signal to build the misunderstanding.")


def choose_tool(activity: Activity) -> Optional[Tool]:
    if activity.id == "listen":
        return TOOLS["headset"]
    if activity.id == "signal":
        return TOOLS["decoder"]
    if activity.id == "repair":
        return TOOLS["headset"]
    return None


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    world = World(setting)
    crew = world.add(Entity(id=params.crew_name, kind="character", type=params.crew_type, meters={}, memes={"curiosity": 1.0}))
    partner = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_type, meters={}, memes={"teamwork": 1.0}))
    tool = choose_tool(activity)

    world.say(f"At {setting.station_name}, {crew.id} was {params.trait} and ready to help.")
    world.say(f"{crew.pronoun().capitalize()} liked {activity.gerund}, because the little ship lights blinked like stars.")
    world.say(f"{partner.id} was there too, and together they were a small team on a space job.")

    world.para()
    world.say(f"One {activity.keyword} hour, {crew.id} and {partner.id} went to {setting.place}.")
    world.say(f"Then they heard {activity.noise} from the comm panel.")
    world.say(f"That strange sound caused a misunderstanding: {activity.misunderstanding}.")

    # Emotional state
    crew.memes["confusion"] = 1.0
    partner.memes["confusion"] = 1.0
    partner.memes["teamwork"] += 1.0

    world.say(f"{crew.id} frowned and looked at {partner.id}.")
    world.say(f'"Do you hear that?" {crew.id} asked. "It sounds like {activity.noise}!"')
    world.say(f"{partner.id} pointed to the panel and said they should not guess too fast.")
    world.say(f"Together, they took a breath and decided to solve it as a team.")

    world.para()
    if tool is None:
        raise StoryError("No matching teamwork tool exists for this activity.")
    world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=crew.id))
    world.say(f'{partner.id} said, "Let\'s {tool.prep} and check the signal carefully."')
    world.say(f"{crew.id} nodded and listened while {partner.id} worked the controls.")
    world.say(f"With {tool.label}, they noticed the sound was not danger at all.")
    world.say(f"It was a helpful signal, and the misunderstanding melted away.")

    crew.memes["confusion"] = 0.0
    crew.memes["joy"] = 1.0
    partner.memes["joy"] = 1.0
    partner.memes["teamwork"] += 1.0

    world.para()
    world.say(f"At last, they {tool.tail} and fixed the problem.")
    world.say(f"The ship timer showed it was still o'clock enough to finish the job.")
    world.say(f"{crew.id} and {partner.id} smiled beside the glowing panel, proud of their teamwork.")
    world.say(f"The little station felt safe again, and the crew was ready for the next space adventure.")

    world.facts.update(
        crew=crew,
        partner=partner,
        tool=tool,
        activity=activity,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story for a small child that includes the word "{f["activity"].keyword}".',
        f"Tell a gentle story about two crew members at {f['setting'].station_name} who solve a misunderstanding with teamwork.",
        f'Write a story where a strange "{f["activity"].noise}" sound turns out to be helpful, not scary.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew: Entity = f["crew"]
    partner: Entity = f["partner"]
    activity: Activity = f["activity"]
    tool: Tool = f["tool"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who were the two crew members at {setting.station_name}?",
            answer=f"The two crew members were {crew.id} and {partner.id}. They worked together at {setting.place}.",
        ),
        QAItem(
            question=f"What strange sound caused the misunderstanding?",
            answer=f"The strange sound was {activity.noise}. It made the crew worry at first, but it was only a clue.",
        ),
        QAItem(
            question="How did the crew solve the problem?",
            answer=f"They used {tool.label} and worked together. Their teamwork helped them understand the signal and fix the issue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What does o'clock mean?",
            answer="O'clock is a way to talk about the exact hour on a clock, like three o'clock.",
        ),
        QAItem(
            question="What can a sound be in a space station?",
            answer="A sound can be a clue, a warning, or a helpful signal from a machine or panel.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class ArgsStoryParams:
    pass


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p, setting in SETTINGS.items():
        for a in setting.affords:
            combos.append((p, a))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with teamwork and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--crew-type", choices=["girl", "boy", "captain", "pilot"])
    ap.add_argument("--partner-type", choices=["girl", "boy", "captain", "pilot"])
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if not combos:
        raise StoryError("No valid setting/activity combination matches the request.")
    place, activity = rng.choice(combos)
    crew_type = args.crew_type or rng.choice(CREW_TYPES)
    partner_type = args.partner_type or rng.choice(CREW_TYPES)
    crew_name = args.name or rng.choice(CREW_NAMES)
    partner_name = args.partner or rng.choice([n for n in CREW_NAMES if n != crew_name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, crew_name=crew_name, crew_type=crew_type,
                       partner_name=partner_name, partner_type=partner_type, trait=trait)


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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="hangar", activity="listen", crew_name="Mira", crew_type="girl", partner_name="Jun", partner_type="boy", trait="curious"),
    StoryParams(place="airlock", activity="signal", crew_name="Ari", crew_type="pilot", partner_name="Tess", partner_type="captain", trait="careful"),
    StoryParams(place="observation", activity="repair", crew_name="Pip", crew_type="boy", partner_name="Rae", partner_type="girl", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} valid space combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
