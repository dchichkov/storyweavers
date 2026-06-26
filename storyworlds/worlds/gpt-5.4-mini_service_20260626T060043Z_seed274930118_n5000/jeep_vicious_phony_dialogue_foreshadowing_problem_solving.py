#!/usr/bin/env python3
"""
storyworlds/worlds/jeep_vicious_phony_dialogue_foreshadowing_problem_solving.py
===============================================================================

A small adventure storyworld about a jeep, a vicious obstacle, and a phony
warning that turns out to hide a real problem. The world is constraint-checked
and built to produce child-friendly stories with dialogue, foreshadowing, and
problem solving.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the trailhead"
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    warning: str
    foreshadow: str
    problem: str
    danger: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str]
    solves: set[str]
    prep: str
    tail: str


@dataclass
class StoryParams:
    place: str
    challenge: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def hero_name_for(gender: str) -> list[str]:
    return ["Ava", "Mia", "Nora", "Zoe", "Lily"] if gender == "girl" else ["Finn", "Leo", "Noah", "Eli", "Max"]


SETTINGS = {
    "ridge": Setting(place="the ridge trail", outdoors=True, affords={"ravine", "storm"}),
    "canyon": Setting(place="the canyon road", outdoors=True, affords={"ravine", "storm"}),
    "forest": Setting(place="the forest track", outdoors=True, affords={"mud", "storm"}),
    "ruins": Setting(place="the old ruins path", outdoors=True, affords={"trap", "storm"}),
}

CHALLENGES = {
    "ravine": Challenge(
        id="ravine",
        verb="cross the ravine",
        gerund="crossing the ravine",
        warning="The path ahead looked smooth, but the ground could open suddenly.",
        foreshadow="A small crack in the dirt zigzagged beside the path like a hint.",
        problem="a gap in the path",
        danger="vicious rocks",
        zone={"feet"},
        tags={"jeep", "vicious", "problem"},
    ),
    "storm": Challenge(
        id="storm",
        verb="push through the storm",
        gerund="rattling through the storm",
        warning="The sky looked bright at first, but the wind kept changing its mind.",
        foreshadow="Far away, the clouds were stacking up like gray towers.",
        problem="a sudden storm",
        danger="vicious wind",
        zone={"body"},
        tags={"jeep", "foreshadowing"},
    ),
    "mud": Challenge(
        id="mud",
        verb="drive through the mud",
        gerund="bumping through the mud",
        warning="The road shone brown and soft, like it wanted to swallow wheels.",
        foreshadow="One tire print sank deeper than the rest.",
        problem="a muddy ditch",
        danger="vicious mud",
        zone={"wheels"},
        tags={"jeep", "problem"},
    ),
    "trap": Challenge(
        id="trap",
        verb="get past the trap",
        gerund="rolling toward the trap",
        warning="The trail looked too neat, almost like someone had made it on purpose.",
        foreshadow="A branch lay across the trail, straight as a ruler.",
        problem="a phony trail marker",
        danger="vicious snare",
        zone={"body"},
        tags={"phony", "foreshadowing"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a rope",
        phrase="a strong rope tied to the jeep",
        protects={"body", "feet"},
        solves={"ravine"},
        prep="tie the rope to the jeep and lower the kids across",
        tail="tugged the rope tight and crossed one careful step at a time",
    ),
    "planks": Tool(
        id="planks",
        label="wooden planks",
        phrase="two flat wooden planks",
        protects={"wheels"},
        solves={"mud"},
        prep="lay the planks under the wheels",
        tail="rolled forward over the planks without sinking",
    ),
    "jacket": Tool(
        id="jacket",
        label="a rain jacket",
        phrase="a bright rain jacket",
        protects={"body"},
        solves={"storm"},
        prep="zip the jacket tight before the storm arrived",
        tail="kept dry while the jeep bumped through the wind",
    ),
    "map": Tool(
        id="map",
        label="a real map",
        phrase="a real map with the trail marked in blue",
        protects={"body"},
        solves={"trap"},
        prep="check the real map instead of the phony sign",
        tail="followed the right turn and skipped the fake path",
    ),
}

GIRL_NAMES = ["Ava", "Mia", "Nora", "Zoe", "Lily"]
BOY_NAMES = ["Finn", "Leo", "Noah", "Eli", "Max"]
TRAITS = ["brave", "curious", "quick-thinking", "steady", "bold"]


def choose_valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for ch in setting.affords:
            for tool_id, tool in TOOLS.items():
                if ch in tool.solves:
                    out.append((place, ch, tool_id))
    return out


def prize_at_risk(challenge: Challenge, tool: Tool) -> bool:
    return challenge.id in tool.solves


def select_tool(challenge: Challenge) -> Optional[Tool]:
    for tool in TOOLS.values():
        if challenge.id in tool.solves:
            return tool
    return None


def explain_rejection(challenge: Challenge, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not solve {challenge.id}. "
        f"The adventure needs a tool that can really handle {challenge.problem}.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.tool:
        ch = CHALLENGES[args.challenge]
        tool = TOOLS[args.tool]
        if not prize_at_risk(ch, tool):
            raise StoryError(explain_rejection(ch, tool))

    combos = [
        c for c in choose_valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, challenge, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(hero_name_for(gender))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        challenge=challenge,
        tool=tool,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: jeep, vicious danger, and a phony clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def world_intro(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait_word', 'brave')} little {hero.type} who loved adventure rides in the jeep."
    )
    world.say(
        f"Every trip with {hero.pronoun('possessive')} {parent.label or parent.type} felt like the start of a quest."
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"joy": 0.0, "trait_word": params.trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"{params.parent}"))
    challenge = CHALLENGES[params.challenge]
    tool = TOOLS[params.tool]
    jeep = world.add(Entity(id="jeep", kind="thing", type="jeep", label="jeep", phrase="their old jeep"))
    tool_ent = world.add(Entity(id=tool.id, kind="thing", type=tool.id, label=tool.label, phrase=tool.phrase, owner=hero.id, caretaker=parent.id))
    tool_ent.worn_by = hero.id
    world.facts.update(hero=hero, parent=parent, challenge=challenge, tool=tool, jeep=jeep, setting=world.setting)
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {parent.label} climbed into the jeep and headed for {world.setting.place}.")
    world.say("The ride bounced and hummed, and the road kept winding like a story waiting to happen.")
    world.para()
    world.say(challenge.foreshadow)
    world.say(
        f"{hero.id} heard {parent.pronoun('possessive')} warning: \"{challenge.warning}\""
    )
    world.say(
        f"That sounded a little phony, because the trail looked calm; but the hint in the dirt made {hero.id} keep looking."
    )
    world.para()
    world.say(
        f"Then the real trouble showed itself: {challenge.problem} with {challenge.danger} under it."
    )
    world.say(
        f"\"We need to think,\" {hero.pronoun('subject')} said. \"The jeep can help, but not if we rush.\""
    )
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.label} talked fast and picked {tool.label}."
    )
    world.say(
        f"{parent.pronoun('subject').capitalize()} said, \"Good eye. We can {tool.prep}.\""
    )
    world.para()
    if params.tool == "map" and params.challenge == "trap":
        world.say(
            f"They checked the map, spotted the phony marker, and turned before the vicious snare could catch them."
        )
    else:
        world.say(f"They worked together to solve the problem.")
    world.say(
        f"At last, {hero.id} {tool.tail}, and the jeep carried them safely on."
    )
    world.say(
        f"{hero.id} smiled at the dark path behind them, because the vicious danger was solved and the phony warning had been understood."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes a jeep, a vicious obstacle, and a phony warning.',
        f"Tell a dialogue-filled story where {f['hero'].id} rides in a jeep, notices a foreshadowing clue, and solves {f['challenge'].problem}.",
        f"Write a brave little adventure about a jeep trip that ends with problem solving instead of panic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    challenge = f["challenge"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who went on the jeep adventure?",
            answer=f"{hero.id} went with {hero.pronoun('possessive')} {parent.label} in the jeep.",
        ),
        QAItem(
            question=f"What did the foreshadowing hint suggest before the real problem appeared?",
            answer=f"It suggested that something strange was ahead on the trail, even though the first warning sounded phony.",
        ),
        QAItem(
            question=f"What problem did they need to solve?",
            answer=f"They needed to solve {challenge.problem}.",
        ),
        QAItem(
            question=f"What tool helped them in the end?",
            answer=f"{tool.label.capitalize()} helped them solve the problem and keep the jeep adventure going.",
        ),
        QAItem(
            question=f"Why did the story mention a phony warning?",
            answer=f"It was there to make the characters look closer, because the first warning was not the whole truth.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "jeep": [
        ("What is a jeep?", "A jeep is a sturdy vehicle that can travel on rough roads and bumpy trails."),
    ],
    "vicious": [
        ("What does vicious mean?", "Vicious means very mean, wild, or dangerous."),
    ],
    "phony": [
        ("What does phony mean?", "Phony means fake or not honest."),
    ],
    "foreshadowing": [
        ("What is foreshadowing in a story?", "Foreshadowing is a clue that hints something important may happen later."),
    ],
    "problem": [
        ("What is problem solving?", "Problem solving is figuring out what to do when something goes wrong."),
    ],
    "dialogue": [
        ("What is dialogue?", "Dialogue is the words characters say to each other in a story."),
    ],
}
KNOWLEDGE_ORDER = ["jeep", "vicious", "phony", "foreshadowing", "problem", "dialogue"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A challenge is risky when the selected tool handles it.
solves(T, C) :- tool(T), challenge(C), tool_solves(T, C).

valid_story(P, C, T) :- setting(P), challenge(C), tool(T), affords(P, C), solves(T, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for ch in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, ch))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for tag in sorted(ch.tags):
            lines.append(asp.fact("tag", cid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for solved in sorted(tool.solves):
            lines.append(asp.fact("tool_solves", tid, solved))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return asp_valid_stories()


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(choose_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches choose_valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="ridge", challenge="ravine", tool="rope", name="Ava", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="forest", challenge="mud", tool="planks", name="Finn", gender="boy", parent="father", trait="curious"),
    StoryParams(place="canyon", challenge="storm", tool="jacket", name="Mia", gender="girl", parent="mother", trait="steady"),
    StoryParams(place="ruins", challenge="trap", tool="map", name="Leo", gender="boy", parent="father", trait="quick-thinking"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible (place, challenge, tool) combos:\n")
        for place, ch, tool in triples:
            print(f"  {place:8} {ch:10} {tool}")
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
            header = f"### {p.name}: {p.challenge} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
