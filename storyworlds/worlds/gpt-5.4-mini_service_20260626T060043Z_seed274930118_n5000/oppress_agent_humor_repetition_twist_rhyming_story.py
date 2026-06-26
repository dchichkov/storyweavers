#!/usr/bin/env python3
"""
storyworlds/worlds/oppress_agent_humor_repetition_twist_rhyming_story.py
========================================================================

A small, constraint-checked story world for a rhyming, humorous tale about
an agent, a silly pressing job, and a twist ending.

Seed inspiration:
- oppress
- agent

Premise:
An agent tries to press down a bouncy troublemaker so the room will stay calm.
The effort is funny, repetitive, and rhyme-friendly, but the twist reveals the
"oppress" job was really about pressing a stamp, not hurting anyone.

The world is designed to generate child-facing, complete stories with:
- Humor
- Repetition
- Twist
- Rhyming Story style
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Objective:
    id: str
    verb: str
    gerund: str
    rush: str
    humor: str
    rhyme_a: str
    rhyme_b: str
    tag: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.beat: int = 0

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.beat = self.beat
        return clone


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    objective: str
    tool: str
    hero_name: str
    hero_type: str
    partner_type: str
    seed: Optional[int] = None


SETTINGS = {
    "hall": Setting(place="the hall", indoor=True, affords={"stamp", "press"}),
    "workshop": Setting(place="the workshop", indoor=True, affords={"stamp", "press"}),
    "courtyard": Setting(place="the courtyard", indoor=False, affords={"stamp", "press"}),
}

OBJECTIVES = {
    "press": Objective(
        id="press",
        verb="press the big button",
        gerund="pressing the big button",
        rush="rush to press the big button",
        humor="the button went boing and sang a ding-dong song",
        rhyme_a="press and dress",
        rhyme_b="gleam and dream",
        tag="press",
    ),
    "stamp": Objective(
        id="stamp",
        verb="stamp the label",
        gerund="stamping the label",
        rush="rush to stamp the label",
        humor="the ink made a wink and a silly little blink",
        rhyme_a="stamp and lamp",
        rhyme_b="note and float",
        tag="stamp",
    ),
    "oppress": Objective(
        id="oppress",
        verb="oppress the squeaky stack",
        gerund="oppressing the squeaky stack",
        rush="rush to oppress the squeaky stack",
        humor="the stack would wobble, bobble, and giggle like a pup",
        rhyme_a="squash and froth",
        rhyme_b="flip and slip",
        tag="oppress",
    ),
}

TOOLS = {
    "stamp_pad": Tool(
        id="stamp_pad",
        label="stamp pad",
        phrase="a bright red stamp pad",
        helps={"stamp"},
    ),
    "brace": Tool(
        id="brace",
        label="bracing block",
        phrase="a bracing block",
        helps={"press", "oppress"},
    ),
    "spring_glove": Tool(
        id="spring_glove",
        label="spring glove",
        phrase="a spring glove",
        helps={"press"},
    ),
    "soft_mat": Tool(
        id="soft_mat",
        label="soft mat",
        phrase="a soft mat",
        helps={"oppress"},
    ),
}

HERO_NAMES = ["Milo", "Nina", "Pip", "Lena", "Toby", "Ivy", "Rae", "Jules"]
CHILD_TYPES = ["girl", "boy"]
PARTNER_TYPES = ["friend", "helper", "pal"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
objective_ok(O) :- objective(O).

tool_ok(T, O) :- tool(T), objective(O), helps(T, O).

valid_story(P, O, T) :- setting(P), objective(O), tool(T), affords(P, O), tool_ok(T, O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid in OBJECTIVES:
        lines.append(asp.fact("objective", oid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for obj_id, obj in OBJECTIVES.items():
            if obj_id not in setting.affords:
                continue
            for tool_id, tool in TOOLS.items():
                if obj_id in tool.helps:
                    combos.append((place, obj_id, tool_id))
    return combos


def choose_tool(obj: Objective) -> Optional[Tool]:
    for tool in TOOLS.values():
        if obj.id in tool.helps:
            return tool
    return None


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}."


def predict(world: World, hero: Entity, obj: Objective) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["desire"] += 1
    sim.get(hero.id).meters[obj.id] = sim.get(hero.id).meters.get(obj.id, 0) + 1
    return {"risky": True}


def setup(world: World, hero: Entity, partner: Entity, obj: Objective, tool: Tool) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a grin so bright, "
        f"and {hero.pronoun('possessive')} {partner.type} liked jokes by night."
    )
    world.say(
        f"At {world.setting.place}, the job was odd but neat: "
        f"{hero.id} had to {obj.verb}, all tidy and complete."
    )
    world.say(
        f"They brought {tool.phrase}, with a bounce and a clack, "
        f"for work that would wobble and jump right back."
    )
    hero.memes["curious"] = 1
    partner.memes["cheer"] = 1
    world.facts.update(hero=hero, partner=partner, objective=obj, tool=tool)


def conflict(world: World, hero: Entity, partner: Entity, obj: Objective) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.para()
    world.say(
        f"{hero.id} said, \"I will {obj.verb}!\" then laughed, \"Zip-zap-zing!\""
    )
    world.say(
        f"{hero.id} tried to {obj.rush}, and the room went ping-ping-ping."
    )
    world.say(
        f"The {obj.tag} part was silly, a squiggle, a jig, "
        f"for every time {hero.id} pressed, the thing did a gig."
    )
    world.say(
        f"{partner.id} warned, \"Take care, dear pal, don't overdo!\" "
        f"But {hero.id} did it again and said, \"I know, I know, doo-doo!\""
    )


def twist(world: World, hero: Entity, partner: Entity, obj: Objective, tool: Tool) -> None:
    world.para()
    world.say(
        f"Then came a twist with a wink and a grin: "
        f"the job was not to push the stack in."
    )
    world.say(
        f"It was a stamp for a sign, a label, a cue, "
        f"and {tool.label} made the ink go through."
    )
    world.say(
        f"So {hero.id} used {tool.label}, with a dip and a dot, "
        f"and the silly little {obj.tag} was not what they got."
    )
    hero.memes["relief"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    partner.memes["joy"] = partner.memes.get("joy", 0) + 1


def resolution(world: World, hero: Entity, partner: Entity, obj: Objective, tool: Tool) -> None:
    world.say(
        f"{hero.id} stamped the page in a neat little row, "
        f"and the letters went click in a happy glow."
    )
    world.say(
        f"\"No need to oppress,\" {partner.id} laughed, \"just press with care!\" "
        f"Then both of them twirled through the warm evening air."
    )
    world.say(
        f"So the agent and pal had a rhyme-full day, "
        f"and the bouncy old trouble just bounced away."
    )


def tell(setting: Setting, obj: Objective, tool: Tool,
         hero_name: str = "Pip", hero_type: str = "boy",
         partner_type: str = "friend") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    partner = world.add(Entity(id="Partner", kind="character", type=partner_type))
    hero.memes["agent"] = 1
    partner.memes["humor"] = 1

    setup(world, hero, partner, obj, tool)
    conflict(world, hero, partner, obj)
    twist(world, hero, partner, obj, tool)
    resolution(world, hero, partner, obj, tool)

    world.facts.update(setting=setting, hero=hero, partner=partner, objective=obj, tool=tool)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["objective"]
    tool = f["tool"]
    return [
        f'Write a short rhyming story for a child about an agent named {hero.id} who must {obj.verb} with {tool.label}.',
        f"Tell a funny repetitive story where an agent tries to {obj.verb} but learns a surprising twist.",
        f'Write a playful rhyme that includes the words "agent" and "{obj.id}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    obj = f["objective"]
    tool = f["tool"]
    place = world.setting.place
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do at {place}?",
            answer=f"{hero.id} was trying to {obj.verb} at {place}, using a funny, careful job.",
        ),
        QAItem(
            question=f"What tool helped {hero.id} finish the job?",
            answer=f"{tool.label} helped {hero.id} finish the job, because it was the right tool for {obj.id}.",
        ),
        QAItem(
            question=f"Who was with {hero.id} during the silly work?",
            answer=f"{partner.id}, {hero.pronoun('possessive')} {partner.type}, was there to watch, warn, and laugh.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=(
                f"The twist was that the job was not really about hurting anything or making a mess; "
                f"it was about stamping a label and doing the work the safe way."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    obj = f["objective"]
    tool = f["tool"]
    out = [
        QAItem(
            question="What does an agent do?",
            answer="An agent is a helper who does an important job, often by following steps carefully.",
        ),
        QAItem(
            question="What is a stamp?",
            answer="A stamp is a tool that presses ink or a mark onto paper so it leaves a shape or word.",
        ),
    ]
    if obj.id == "oppress":
        out.append(
            QAItem(
                question="What does oppress mean in this story?",
                answer="In this story, oppress is a pretend, silly word for pressing a bouncy stack too hard, but the twist shows the real job was safer than that.",
            )
        )
    if tool.id == "stamp_pad":
        out.append(
            QAItem(
                question="What is a stamp pad for?",
                answer="A stamp pad holds ink so a stamp can make a clear mark on paper.",
            )
        )
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with an agent, humor, repetition, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--objective", choices=OBJECTIVES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--partner", choices=PARTNER_TYPES)
    ap.add_argument("--name")
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


def valid_story_params(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.objective:
        combos = [c for c in combos if c[1] == args.objective]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_story_params(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, objective, tool = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(CHILD_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    partner_type = args.partner or rng.choice(PARTNER_TYPES)
    return StoryParams(
        place=place,
        objective=objective,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        partner_type=partner_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        OBJECTIVES[params.objective],
        TOOLS[params.tool],
        params.hero_name,
        params.hero_type,
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


CURATED = [
    StoryParams(place="hall", objective="press", tool="spring_glove", hero_name="Pip", hero_type="boy", partner_type="friend"),
    StoryParams(place="workshop", objective="stamp", tool="stamp_pad", hero_name="Nina", hero_type="girl", partner_type="helper"),
    StoryParams(place="courtyard", objective="oppress", tool="soft_mat", hero_name="Milo", hero_type="boy", partner_type="pal"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, objective, tool) combos:\n")
        for place, obj, tool in stories:
            print(f"  {place:10} {obj:9} {tool}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.objective} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
