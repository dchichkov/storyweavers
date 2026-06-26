#!/usr/bin/env python3
"""
storyworlds/worlds/northern_anaconda_wit_problem_solving_pirate_tale.py
======================================================================

A small pirate-tale storyworld about a clever crew, a northern route, and a
tricky anaconda problem that can only be solved with wit.

The world is built from a simple source-tale premise:
- A pirate crew sails north to reach a trade cove.
- A giant anaconda blocks the only safe passage through a narrow ice strait.
- Bluster fails, so the crew must use wit, rope, and a calm plan.
- The ending proves the problem was solved without a fight.

This world is intentionally small and constraint-checked:
- typed entities have physical meters and emotional memes
- state drives narration
- invalid explicit choices raise StoryError
- an inline ASP twin mirrors the reasonableness gate
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess", "pirate-woman"}
        male = {"boy", "man", "father", "captain", "pirate-man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the northern strait"
    chill: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    name: str
    danger: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    works_on: set[str]
    consumes: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.sea_state: str = "calm"
        self.route_blocked: bool = False
        self.anaconda_spotted: bool = False
        self.plan_made: bool = False
        self.plan_succeeded: bool = False

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.sea_state = self.sea_state
        clone.route_blocked = self.route_blocked
        clone.anaconda_spotted = self.anaconda_spotted
        clone.plan_made = self.plan_made
        clone.plan_succeeded = self.plan_succeeded
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    captain_name: str
    problem: str
    tool: str
    seed: Optional[int] = None


SETTINGS = {
    "northern_strait": Setting(place="the northern strait", chill=True, affords={"sail"}),
    "ice_cove": Setting(place="the ice cove", chill=True, affords={"sail", "dock"}),
    "foggy_bay": Setting(place="the foggy bay", chill=True, affords={"sail"}),
}

PROBLEMS = {
    "anaconda": Problem(
        id="anaconda",
        name="a giant anaconda",
        danger="blocked the narrow waterway",
        fix_hint="a calm plan could guide it away",
        tags={"anaconda", "northern", "wit"},
    ),
}

TOOLS = {
    "harpoon": Tool(
        id="harpoon",
        label="a harpoon",
        phrase="a long harpoon with a bright rope tied to it",
        use_line="cast the rope past the snake and tug it toward the reeds",
        works_on={"anaconda"},
    ),
    "drum": Tool(
        id="drum",
        label="a drum",
        phrase="a hollow drum",
        use_line="beat a steady rhythm to lure the snake toward the sheltered shore",
        works_on={"anaconda"},
    ),
    "bait": Tool(
        id="bait",
        label="a fish basket",
        phrase="a fish basket full of shiny mackerel",
        use_line="set the bait where the snake could safely follow it",
        works_on={"anaconda"},
    ),
}

GIRL_NAMES = ["Nina", "Mira", "Luna", "Ada", "Sora", "Ivy"]
BOY_NAMES = ["Finn", "Jory", "Milo", "Tate", "Cade", "Oren"]
CAPTAIN_NAMES = ["Captain Marla", "Captain Reed", "Captain Vale", "Captain Jo"]


def problem_risky(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.works_on


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prob_id, prob in PROBLEMS.items():
            for tool_id, tool in TOOLS.items():
                if problem_risky(prob, tool):
                    out.append((place, prob_id, tool_id))
    return out


def introduce(world: World, hero: Entity, captain: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} aboard {captain.label}, and the crew said "
        f"{hero.id} had a sharp wit for tricky days."
    )


def set_sail(world: World, hero: Entity, captain: Entity, setting: Setting) -> None:
    world.say(
        f"One day, the ship sailed into {setting.place}, where the wind bit cold and "
        f"the water looked silver under the clouds."
    )


def spot_problem(world: World, hero: Entity, prob: Problem) -> None:
    world.anaconda_spotted = True
    world.route_blocked = True
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say(
        f"Then {prob.name} rose from the dark water and {prob.danger}."
    )
    world.say(
        f"The crew had to stop, because the path ahead would not be safe until someone solved it."
    )


def think(world: World, hero: Entity, captain: Entity, prob: Problem) -> None:
    hero.memes["thinking"] = hero.memes.get("thinking", 0.0) + 1
    captain.memes["worry"] = captain.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} did not shout. {hero.pronoun().capitalize()} watched the snake, the rocks, and the tides, "
        f"and {hero.pronoun()} thought with careful wit."
    )
    world.say(
        f"{captain.label} asked for a brave idea, not a loud one."
    )


def choose_tool(world: World, hero: Entity, prob: Problem, tool: Tool) -> Entity:
    if prob.id not in tool.works_on:
        raise StoryError(f"{tool.label} is not a sensible fix for {prob.name}.")
    tool_ent = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=hero.id,
    ))
    tool_ent.carried_by = hero.id
    world.say(
        f"{hero.id} picked up {tool.phrase}."
    )
    return tool_ent


def test_plan(world: World, hero: Entity, prob: Problem, tool: Tool) -> bool:
    sim = world.copy()
    sim.plan_made = True
    if tool.id == "harpoon":
        sim.route_blocked = False
        sim.plan_succeeded = True
    elif tool.id == "drum":
        sim.route_blocked = False
        sim.plan_succeeded = True
    elif tool.id == "bait":
        sim.route_blocked = False
        sim.plan_succeeded = True
    else:
        sim.plan_succeeded = False
    return sim.plan_succeeded


def act(world: World, hero: Entity, captain: Entity, prob: Problem, tool: Tool) -> None:
    world.plan_made = True
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    world.say(
        f"At last, {hero.id} gave the crew a plan: {tool.use_line}."
    )
    world.say(
        f"The captain nodded, and the sailors worked together without panic."
    )
    world.route_blocked = False
    world.plan_succeeded = True


def resolve(world: World, hero: Entity, captain: Entity, prob: Problem) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    captain.memes["relief"] = captain.memes.get("relief", 0.0) + 1
    world.say(
        f"The anaconda slid away from the channel, and the ship could sail through at last."
    )
    world.say(
        f"{hero.id}'s clever idea had turned a stuck voyage into a safe one."
    )
    world.say(
        f"By sunset, the crew was moving north again, and the water behind them was open and calm."
    )


def tell(setting: Setting, problem: Problem, tool: Tool,
         hero_name: str, hero_type: str, captain_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id=captain_name, kind="character", type="captain", label=captain_name))
    world.facts["hero"] = hero
    world.facts["captain"] = captain
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["setting"] = setting

    introduce(world, hero, captain)
    world.para()
    set_sail(world, hero, captain, setting)
    spot_problem(world, hero, problem)
    think(world, hero, captain, problem)
    tool_ent = choose_tool(world, hero, problem, tool)
    world.facts["tool_ent"] = tool_ent
    if not test_plan(world, hero, problem, tool):
        raise StoryError("The chosen plan does not solve the problem.")
    act(world, hero, captain, problem, tool)
    resolve(world, hero, captain, problem)
    return world


KNOWLEDGE = {
    "northern": [
        (
            "What does northern mean?",
            "Northern means toward the north, the colder direction on a map."
        )
    ],
    "anaconda": [
        (
            "What is an anaconda?",
            "An anaconda is a very large snake. It can squeeze its body tightly and swim well."
        )
    ],
    "wit": [
        (
            "What is wit?",
            "Wit is quick clever thinking that helps someone solve a problem in a smart way."
        )
    ],
    "rope": [
        (
            "What is rope used for?",
            "Rope can tie things, pull things, or help people hold on safely."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    problem = f["problem"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        f'Write a short pirate tale for a young child set in {setting.place} that uses the word "northern".',
        f"Tell a story where {hero.id} and {captain.label} meet {problem.name} and solve the trouble with wit.",
        f"Write a gentle adventure about a pirate crew, a big snake, and a clever plan using {tool.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    problem = f["problem"]
    tool = f["tool"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the clever pirate child in the story?",
            answer=f"It was {hero.id}, a little {hero.type} aboard {captain.label}."
        ),
        QAItem(
            question=f"What blocked the ship in {setting.place}?",
            answer=f"{problem.name} blocked the narrow waterway and made the crew stop."
        ),
        QAItem(
            question=f"How did {hero.id} help solve the problem?",
            answer=f"{hero.id} used wit and chose {tool.label} for a careful plan."
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer="The anaconda moved away, the path opened, and the ship sailed on safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    out: list[QAItem] = []
    for tag in ["northern", "anaconda", "wit", "rope"]:
        if tag in tags or tag == "rope":
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:16} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  route_blocked={world.route_blocked}")
    lines.append(f"  anaconda_spotted={world.anaconda_spotted}")
    lines.append(f"  plan_made={world.plan_made}")
    lines.append(f"  plan_succeeded={world.plan_succeeded}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} is not a reasonable way to solve {problem.name}; "
        f"the plan must actually fit the problem.)"
    )


ASP_RULES = r"""
% A problem is solvable with a tool when the tool is known to work on it.
solvable(P, T) :- problem(P), tool(T), works_on(T, P).

% A valid story is one where the place can host the sailing scene and the
% problem/tool pair is solvable.
valid(Place, P, T) :- setting(Place), problem(P), tool(T), solvable(P, T).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.chill:
            lines.append(asp.fact("chill", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.works_on):
            lines.append(asp.fact("works_on", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    asp_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale storyworld: northern waters, anaconda trouble, and wit."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--captain")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.problem and args.tool:
        prob = PROBLEMS[args.problem]
        tool = TOOLS[args.tool]
        if not problem_risky(prob, tool):
            raise StoryError(explain_rejection(prob, tool))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain_name = args.captain or rng.choice(CAPTAIN_NAMES)
    hero_type = "girl" if gender == "girl" else "boy"
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        captain_name=captain_name,
        problem=problem,
        tool=tool,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        params.hero_name,
        params.hero_type,
        params.captain_name,
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
    StoryParams(
        place="northern_strait",
        hero_name="Nina",
        hero_type="girl",
        captain_name="Captain Marla",
        problem="anaconda",
        tool="drum",
    ),
    StoryParams(
        place="ice_cove",
        hero_name="Finn",
        hero_type="boy",
        captain_name="Captain Reed",
        problem="anaconda",
        tool="harpoon",
    ),
    StoryParams(
        place="foggy_bay",
        hero_name="Milo",
        hero_type="boy",
        captain_name="Captain Vale",
        problem="anaconda",
        tool="bait",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, tool) combos:\n")
        for place, problem, tool in combos:
            print(f"  {place:15} {problem:10} {tool}")
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
            header = f"### {p.hero_name}: {p.problem} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
