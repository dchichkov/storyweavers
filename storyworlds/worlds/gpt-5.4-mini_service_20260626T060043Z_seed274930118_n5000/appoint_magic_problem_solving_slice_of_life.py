#!/usr/bin/env python3
"""
A tiny slice-of-life storyworld about a community of little mages who solve
ordinary problems by appointing the right helper for the job.

Premise:
- Someone notices a small everyday problem.
- A calm adult or friend appoints a helper or a role.
- The chosen helper uses a bit of magic in a careful, practical way.
- The problem gets solved with a satisfying, gentle ending image.

This world stays close to slice-of-life: small rooms, simple chores, friendly
talk, and a magical toolset that behaves like practical household help.
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
# World model
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
    role: str = ""
    magical: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "woman": {"subject": "she", "object": "her", "possessive": "her"},
            "man": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    @property
    def display(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    noun: str
    verb: str
    trouble: str
    visible: str
    tag: str
    zone: str
    urgency: str
    can_magically_fix: bool = True


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    verb: str
    result: str
    tone: str
    role: str


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.used_magic: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"spill", "stuck_drawer", "missing_spoon"}),
    "laundry_room": Setting(place="the laundry room", indoor=True, affords={"sock_mismatch", "spill"}),
    "garden": Setting(place="the garden", indoor=False, affords={"wilted_flower", "tangled_vines"}),
    "workshop": Setting(place="the workshop", indoor=True, affords={"stuck_drawer", "broken_tag"}),
    "porch": Setting(place="the porch", indoor=False, affords={"lost_note", "drip"}),
}

PROBLEMS = {
    "spill": Problem(
        id="spill",
        noun="spill",
        verb="clean up a spill",
        trouble="a little puddle of juice on the floor",
        visible="a shiny little puddle",
        tag="spill",
        zone="floor",
        urgency="before someone steps in it",
    ),
    "stuck_drawer": Problem(
        id="stuck_drawer",
        noun="drawer",
        verb="open the stuck drawer",
        trouble="a drawer that would not slide open",
        visible="a wooden drawer that sat crooked in its frame",
        tag="drawer",
        zone="table",
        urgency="before the scissors inside were needed",
    ),
    "missing_spoon": Problem(
        id="missing_spoon",
        noun="spoon",
        verb="find the missing spoon",
        trouble="a spoon that had gone missing from the tea tray",
        visible="an empty spoon spot in the tray",
        tag="spoon",
        zone="table",
        urgency="before tea cooled down",
    ),
    "sock_mismatch": Problem(
        id="sock_mismatch",
        noun="sock",
        verb="match the socks",
        trouble="a basket of mixed-up socks",
        visible="two lonely piles of tiny socks",
        tag="sock",
        zone="basket",
        urgency="before school time",
    ),
    "wilted_flower": Problem(
        id="wilted_flower",
        noun="flower",
        verb="help the flower stand up",
        trouble="a wilted flower with a droopy head",
        visible="one bent flower in the garden bed",
        tag="flower",
        zone="garden",
        urgency="before the sun climbed higher",
    ),
    "tangled_vines": Problem(
        id="tangled_vines",
        noun="vines",
        verb="untangle the vines",
        trouble="a knot of vines around the fence",
        visible="green stems looped together like string",
        tag="vine",
        zone="fence",
        urgency="before the gate could swing shut",
    ),
    "broken_tag": Problem(
        id="broken_tag",
        noun="tag",
        verb="fix the broken tag",
        trouble="a name tag that had fallen off a plant pot",
        visible="a tag lying face-up on the bench",
        tag="tag",
        zone="bench",
        urgency="before the plant got misplaced",
    ),
    "lost_note": Problem(
        id="lost_note",
        noun="note",
        verb="find the lost note",
        trouble="a note with the shopping list that had blown away",
        visible="one corner of paper under the mat",
        tag="note",
        zone="door",
        urgency="before the market trip",
    ),
    "drip": Problem(
        id="drip",
        noun="drip",
        verb="stop the drip",
        trouble="a tiny drip from the porch roof",
        visible="one steady drop from the gutter",
        tag="water",
        zone="roof",
        urgency="before the bucket overflowed",
    ),
}

TOOLS = [
    MagicTool(
        id="glow-broom",
        label="a glow broom",
        phrase="a broom that hummed softly and swept by itself",
        solves={"spill"},
        verb="glow and sweep",
        result="the floor shone clean",
        tone="bright",
        role="cleanup helper",
    ),
    MagicTool(
        id="unwinding-glove",
        label="an unwinding glove",
        phrase="a glove that loosened knots with a gentle tug",
        solves={"stuck_drawer", "tangled_vines"},
        verb="unwind",
        result="the wood slid free and the vines relaxed",
        tone="patient",
        role="tangle helper",
    ),
    MagicTool(
        id="finding-lantern",
        label="a finding lantern",
        phrase="a lantern that glowed warmer when it was near a lost thing",
        solves={"missing_spoon", "lost_note"},
        verb="search",
        result="the lost thing was found right away",
        tone="soft",
        role="finder",
    ),
    MagicTool(
        id="pairing-charms",
        label="pairing charms",
        phrase="two tiny charms that nudged matching things together",
        solves={"sock_mismatch"},
        verb="pair",
        result="the socks made happy little pairs",
        tone="careful",
        role="matcher",
    ),
    MagicTool(
        id="lift-spell",
        label="a lift spell",
        phrase="a spell that lifted droopy things without hurting them",
        solves={"wilted_flower"},
        verb="lift",
        result="the flower stood up straight again",
        tone="gentle",
        role="care helper",
    ),
    MagicTool(
        id="drip-stop",
        label="a drip-stop charm",
        phrase="a charm that caught water drops before they fell too far",
        solves={"drip"},
        verb="catch",
        result="the drip slowed to a tiny, safe trickle",
        tone="steady",
        role="repair helper",
    ),
]

NAMES = ["Mina", "Owen", "Lio", "Nina", "Pip", "Tess", "Arlo", "Jade", "Rae", "Theo"]
ROLES = ["caretaker", "helper", "assistant", "finder", "fixer", "captain"]
ADJECTIVES = ["calm", "careful", "kind", "clever", "steady", "patient"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    role_name: str
    adjective: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is solvable when a tool solves its tag.
solvable(P) :- problem(P), tags(P, T), toolsolves(T, _).

% A valid story needs a place that affords the problem and a matching tool.
valid_story(Place, Prob, Tool) :- setting(Place), affords(Place, Prob),
                                  problem(Prob), tool(Tool), tags(Prob, T),
                                  toolsolves(T, Tool).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for p in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("tags", pid, prob.tag))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for s in sorted(tool.solves):
            lines.append(asp.fact("toolsolves", s, tool.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(python_set)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(asp_set - python_set))
    print("only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for prob_id in setting.affords:
            prob = PROBLEMS[prob_id]
            for tool in TOOLS:
                if prob.tag in tool.solves:
                    combos.append((place, prob_id, tool.id))
    return combos


def explain_rejection(prob: Problem) -> str:
    return (
        f"(No story: nothing in the toolset reasonably solves {prob.trouble}. "
        f"The world only appoints helpers for problems they can actually fix.)"
    )


# ---------------------------------------------------------------------------
# World building / narration
# ---------------------------------------------------------------------------

def choose_tool(problem: Problem) -> MagicTool:
    for tool in TOOLS:
        if problem.tag in tool.solves:
            return tool
    raise StoryError(explain_rejection(problem))


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    problem = PROBLEMS[params.problem]
    tool = choose_tool(problem)

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        role=params.role_name,
        meters={"calm": 1.0},
        memes={"worry": 0.0, "pride": 0.0, "relief": 0.0},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type="woman",
        label="the grown-up",
        role="appointing helper",
    ))
    prob_ent = world.add(Entity(
        id=problem.id,
        kind="thing",
        type=problem.noun,
        label=problem.noun,
        phrase=problem.trouble,
        caretaker=caretaker.id,
        role=problem.tag,
        meters={"trouble": 1.0},
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
        magical=True,
        role=tool.role,
    ))

    world.facts.update(hero=hero, caretaker=caretaker, problem=prob_ent, tool=tool_ent,
                       tool_def=tool, problem_def=problem, params=params)

    world.say(f"{hero.id} was a {params.adjective} little {params.gender} who liked quiet afternoons and small jobs that needed doing.")
    world.say(f"{hero.id} had the role of {params.role_name}, which meant {hero.pronoun('subject')} kept an eye on little things around {world.setting.place}.")
    world.say(f"One day, {hero.id} noticed {problem.visible}, and the little trouble made the room feel stuck.")

    world.para()
    world.say(f'"Let me appoint someone," said {caretaker.display}, and {caretaker.pronoun("subject")} pointed to {hero.id}.')
    world.say(f'"I appoint {hero.id} as the {tool.role}," {caretaker.display} said, handing over {tool.label}.')
    world.say(f'{tool.label.capitalize()} felt warm in {hero.pronoun("possessive")} hands, as if it already knew what to do.')

    world.para()
    world.say(f'{hero.id} took a slow breath and used {tool.label} to {tool.verb}.')
    world.say(f'Soft magic answered at once: {tool.result}.')
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    hero.memes["pride"] = 1.0
    prob_ent.meters["trouble"] = 0.0
    tool_ent.meters["glow"] = 1.0
    world.used_magic.add(tool.id)

    world.para()
    if problem.id == "spill":
        world.say(f"The floor was dry again, and the small room smelled like soap instead of juice.")
    elif problem.id == "stuck_drawer":
        world.say(f"The drawer opened with a tiny sigh, and the scissors sat neatly inside like they had been waiting to wake up.")
    elif problem.id == "missing_spoon":
        world.say(f"The spoon was found tucked behind the tea tray, and the tea could finally be served.")
    elif problem.id == "sock_mismatch":
        world.say(f"The socks sat in matching pairs, with no lonely ones left in the basket.")
    elif problem.id == "wilted_flower":
        world.say(f"The flower lifted its head toward the light, and the garden looked glad again.")
    elif problem.id == "tangled_vines":
        world.say(f"The vines loosened around the fence, and the gate could swing open with ease.")
    elif problem.id == "broken_tag":
        world.say(f"The tag was placed back on the pot, and the plant had its name again.")
    elif problem.id == "lost_note":
        world.say(f"The note was safe in {caretaker.pronoun('possessive')} pocket, and the market list was ready to use.")
    elif problem.id == "drip":
        world.say(f"The drip became a shy little trickle, and the porch stayed tidy and calm.")
    else:
        world.say(f"The little problem was gone, and the day went on feeling easy.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prob = f["problem_def"]
    tool = f["tool_def"]
    return [
        f'Write a short slice-of-life story for a child where someone appoints {hero.id} to fix a small problem using magic.',
        f"Tell a gentle story about {hero.id}, a {params_word(hero.role)}, who uses {tool.label} to solve {prob.noun} trouble at {world.setting.place}.",
        f'Write a calm story that includes the word "appoint" and ends with a small everyday task being magically solved.',
    ]


def params_word(role: str) -> str:
    return role if role else "helper"


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    problem = f["problem_def"]
    tool = f["tool_def"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was appointed to help with the {problem.noun} problem?",
            answer=f"{caretaker.display} appointed {hero.id} to help, because {hero.id} was already acting like the {tool.role}.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice at {place}?",
            answer=f"{hero.id} noticed {problem.trouble} at {place}, and it made the day feel a little stuck.",
        ),
        QAItem(
            question=f"What magic tool did {hero.id} use to solve the problem?",
            answer=f"{hero.id} used {tool.label}, which was {tool.phrase}, and it solved the problem by {tool.verb}.",
        ),
        QAItem(
            question=f"How did the story end after the magic helped?",
            answer=f"The ending was calm and tidy: {tool.result}, and the little problem was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool = f["tool_def"]
    prob = f["problem_def"]
    out = [
        QAItem(
            question="What does it mean to appoint someone?",
            answer="To appoint someone means to choose them for a job or role.",
        ),
        QAItem(
            question="What is a simple way magic can help in a story?",
            answer="Magic can help by making a hard job easier, like finding things or cleaning up a mess.",
        ),
    ]
    if prob.tag in tool.solves:
        out.append(QAItem(
            question=f"Why was {tool.label} the right tool for this problem?",
            answer=f"It was right because it could help with {prob.trouble} and turn it into an easy fix.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.magical:
            bits.append("magical=True")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) " + " ".join(bits))
    lines.append(f"  used_magic={sorted(world.used_magic)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life magical problem-solving storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role-name", choices=ROLES)
    ap.add_argument("--adjective", choices=ADJECTIVES)
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
    if args.problem:
        prob = PROBLEMS[args.problem]
        if not any(p == args.problem for _, p, _ in combos):
            raise StoryError(explain_rejection(prob))
    viable = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.problem is None or c[1] == args.problem)
    ]
    if not viable:
        raise StoryError("(No valid story matches the given options.)")
    place, problem, _tool = rng.choice(sorted(viable))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    role_name = args.role_name or rng.choice(ROLES)
    adjective = args.adjective or rng.choice(ADJECTIVES)
    return StoryParams(place=place, problem=problem, name=name, gender=gender, role_name=role_name, adjective=adjective)


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="kitchen", problem="spill", name="Mina", gender="girl", role_name="helper", adjective="careful"),
    StoryParams(place="workshop", problem="stuck_drawer", name="Owen", gender="boy", role_name="fixer", adjective="steady"),
    StoryParams(place="laundry_room", problem="sock_mismatch", name="Tess", gender="girl", role_name="finder", adjective="kind"),
    StoryParams(place="garden", problem="wilted_flower", name="Arlo", gender="boy", role_name="caretaker", adjective="calm"),
    StoryParams(place="porch", problem="lost_note", name="Rae", gender="girl", role_name="assistant", adjective="clever"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_show_program() -> str:
    return asp_program("#show valid_story/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} valid story combos")
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
