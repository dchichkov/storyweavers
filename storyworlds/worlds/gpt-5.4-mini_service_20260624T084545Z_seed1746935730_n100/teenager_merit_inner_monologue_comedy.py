#!/usr/bin/env python3
"""
storyworlds/worlds/teenager_merit_inner_monologue_comedy.py
==========================================================

A small comedy storyworld about a teenager trying to earn merit and accidentally
thinking far too loudly in their own head.

Premise:
- A teenager wants merit from a grown-up or school authority.
- The teenager's inner monologue keeps them from doing something embarrassing.
- A small mix-up creates a comic turn.
- The teenager chooses a sensible, honest fix and ends with actual merit.

The simulated world tracks physical items and emotional state:
- meters: badges, papers, stains, tidy, distance, etc.
- memes: worry, pride, embarrassment, resolve, merit, relief, amusement

The story is intentionally state-driven, so the prose changes with the model.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    verb: str
    gerund: str
    mishap: str
    consequence: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Merit:
    id: str
    label: str
    phrase: str
    kind: str
    region: str = "torso"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    remedy: str
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


@dataclass
class StoryParams:
    place: str
    goal: str
    merit: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "classroom": Setting(place="the classroom", affords={"presentation", "cleanup", "apology"}),
    "hallway": Setting(place="the hallway", affords={"presentation", "cleanup", "apology"}),
    "library": Setting(place="the library", affords={"presentation", "cleanup", "apology"}),
}

GOALS = {
    "presentation": Goal(
        id="presentation",
        verb="give a presentation",
        gerund="giving a presentation",
        mishap="speaking too fast",
        consequence="jumbling the facts",
        keyword="presentation",
        tags={"school", "speech"},
    ),
    "cleanup": Goal(
        id="cleanup",
        verb="help clean up",
        gerund="helping clean up",
        mishap="carrying too many books",
        consequence="dropping a stack with a ridiculous flop",
        keyword="cleanup",
        tags={"school", "help"},
    ),
    "apology": Goal(
        id="apology",
        verb="apologize first",
        gerund="apologizing first",
        mishap="staring at the floor",
        consequence="forgetting the brave part",
        keyword="apology",
        tags={"school", "sorry"},
    ),
}

MERITS = {
    "badge": Merit(
        id="badge",
        label="merit badge",
        phrase="a shiny merit badge",
        kind="badge",
        region="torso",
    ),
    "certificate": Merit(
        id="certificate",
        label="certificate",
        phrase="a neat certificate with gold letters",
        kind="paper",
        region="torso",
    ),
    "star": Merit(
        id="star",
        label="gold star",
        phrase="a gold star sticker",
        kind="sticker",
        region="torso",
    ),
}

TOOLS = {
    "note": Tool(
        id="note",
        label="a small note card",
        prep="write the main points on a small note card",
        remedy="held a note card with three simple facts",
        protects={"speech"},
    ),
    "box": Tool(
        id="box",
        label="a cardboard box",
        prep="put the books in a cardboard box",
        remedy="used a box to carry the stack safely",
        protects={"help"},
    ),
    "breath": Tool(
        id="breath",
        label="a deep breath",
        prep="take one deep breath and look up",
        remedy="took a deep breath and tried again",
        protects={"sorry"},
    ),
}

TEEN_NAMES = ["Maya", "Noah", "Lina", "Owen", "Zara", "Eli", "Nina", "Theo"]
TRAITS = ["awkward", "brave", "curious", "earnest", "dramatic", "hopeful"]
ADULTS = ["teacher", "coach", "librarian"]


def reasonableness(goal: Goal, merit: Merit) -> bool:
    return goal.kind_matches if False else True


def goal_needs_support(goal: Goal, merit: Merit) -> bool:
    return merit.region == "torso"


def select_tool(goal: Goal, merit: Merit) -> Optional[Tool]:
    for tool in TOOLS.values():
        if goal.tags & tool.protects:
            return tool
    return None


def _do_goal(world: World, actor: Entity, goal: Goal, narrate: bool = True) -> None:
    actor.memes["effort"] = actor.memes.get("effort", 0.0) + 1
    if goal.id == "presentation":
        actor.memes["anxiety"] = actor.memes.get("anxiety", 0.0) + 1
    if goal.id == "cleanup":
        actor.meters["carried"] = actor.meters.get("carried", 0.0) + 1
    if goal.id == "apology":
        actor.memes["embarrassment"] = actor.memes.get("embarrassment", 0.0) + 1


def predict_mishap(world: World, actor: Entity, goal: Goal, merit_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
        "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by, "plural": v.plural,
        "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    _do_goal(sim, sim.get(actor.id), goal, narrate=False)
    merit = sim.get(merit_id)
    return {
        "ruined": sim.get(actor.id).memes.get("anxiety", 0.0) >= THRESHOLD and goal.id == "presentation" and merit.kind == "paper",
        "embarrassing": True if goal.id in {"presentation", "cleanup", "apology"} else False,
    }


def establish(world: World, teen: Entity) -> None:
    trait = next(t for t in teen.meters.keys() if False) if False else ""
    world.say(f"{teen.id} was a teenager who wanted to do well without becoming a walking disaster.")


def introduce_inner_voice(world: World, teen: Entity, goal: Goal) -> None:
    world.say(
        f"Inside {teen.id}'s head, a tiny announcer was already heckling the plan: "
        f'"What if you {goal.mishap}? What if everyone notices?"'
    )


def arrive(world: World, teen: Entity, adult: Entity, goal: Goal, merit: Merit) -> None:
    world.say(
        f"One day, {teen.id} went to {world.setting.place} with {goal.verb} on {teen.pronoun('possessive')} mind."
    )
    world.say(
        f"{teen.id} wanted {merit.phrase}, and {teen.pronoun().capitalize()} could almost hear it sparkling in the future."
    )


def worry(world: World, teen: Entity, adult: Entity, goal: Goal, merit: Merit) -> None:
    teen.memes["worry"] = teen.memes.get("worry", 0.0) + 1
    world.say(
        f"{teen.id} thought, 'Stay calm, me. We are a serious expert in not tripping over air.'"
    )
    world.say(
        f"Then {teen.id} noticed {adult.label} watching and immediately felt one inch taller and three inches sillier."
    )


def warning(world: World, adult: Entity, teen: Entity, goal: Goal, merit: Merit) -> None:
    teen.memes["merit_hunger"] = teen.memes.get("merit_hunger", 0.0) + 1
    world.say(
        f'"If you want {merit.phrase}, you need to do this the careful way," {adult.label} said.'
    )
    world.say(
        f"{teen.id} nodded like a professional listener while {teen.pronoun('possessive')} brain shouted, "
        f"'Careful is my favorite kind of panic.'"
    )


def comic_mishap(world: World, teen: Entity, goal: Goal, merit: Merit) -> None:
    teen.memes["embarrassment"] = teen.memes.get("embarrassment", 0.0) + 1
    if goal.id == "presentation":
        world.say(
            f"{teen.id} started to {goal.verb}, but the first sentence came out like a bicycle with a loose bell."
        )
    elif goal.id == "cleanup":
        world.say(
            f"{teen.id} tried to {goal.verb}, but the stack of books gave a heroic wobble and then a dramatic flop."
        )
    else:
        world.say(
            f"{teen.id} tried to {goal.verb}, but {teen.pronoun('possessive')} eyes got stuck on the floor like glue."
        )


def inner_monologue(world: World, teen: Entity, goal: Goal) -> None:
    world.say(
        f"Inside, {teen.id} thought, 'This is fine. The audience loves confidence. Also, the audience may be imaginary.'"
    )


def offer_fix(world: World, adult: Entity, teen: Entity, goal: Goal, merit: Merit) -> Optional[Tool]:
    tool = select_tool(goal, merit)
    if tool is None:
        return None
    world.say(
        f"{adult.label} smiled and said, 'How about you {tool.prep} first?'"
    )
    return tool


def accept_fix(world: World, teen: Entity, adult: Entity, goal: Goal, merit: Merit, tool: Tool) -> None:
    teen.memes["resolve"] = teen.memes.get("resolve", 0.0) + 1
    teen.memes["worry"] = max(0.0, teen.memes.get("worry", 0.0) - 1)
    world.say(
        f"{teen.id} took a breath and thought, 'Aha. A plan. A miraculous object made of not-failing.'"
    )
    world.say(
        f"{teen.id} did it again, this time {tool.remedy}, and the room rewarded {teen.pronoun('object')} with real applause."
    )
    world.say(
        f"By the end, {teen.id} earned {merit.phrase}, and even the tiny announcer in {teen.pronoun('possessive')} head took a bow."
    )


def tell(setting: Setting, goal: Goal, merit_cfg: Merit,
         name: str, gender: str, adult_type: str, trait: str) -> World:
    world = World(setting)
    teen = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        owner=None,
        meters={"age": 1.0},
        memes={"merit": 0.0, "worry": 0.0},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label=f"the {adult_type}",
    ))
    merit = world.add(Entity(
        id="Merit",
        type=merit_cfg.kind,
        label=merit_cfg.label,
        phrase=merit_cfg.phrase,
        owner=teen.id,
        plural=merit_cfg.plural,
        meters={"shine": 1.0},
    ))

    establish(world, teen)
    introduce_inner_voice(world, teen, goal)
    arrive(world, teen, adult, goal, merit_cfg)

    world.para()
    worry(world, teen, adult, goal, merit_cfg)
    warning(world, adult, teen, goal, merit_cfg)
    comic_mishap(world, teen, goal, merit_cfg)
    inner_monologue(world, teen, goal)

    world.para()
    tool = offer_fix(world, adult, teen, goal, merit_cfg)
    if tool is None:
        raise StoryError("No reasonable comedy fix exists for this goal and merit item.")
    accept_fix(world, teen, adult, goal, merit_cfg, tool)

    teen.memes["merit"] = 1.0
    world.facts.update(
        teen=teen,
        adult=adult,
        merit=merit,
        goal=goal,
        tool=tool,
        resolved=True,
        trait=trait,
    )
    return world


SETTINGS_BY_NAME = SETTINGS
GOALS_BY_NAME = GOALS
MERITS_BY_NAME = MERITS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for gid in setting.affords:
            goal = GOALS[gid]
            for mid, merit in MERITS.items():
                if goal_needs_support(goal, merit) and select_tool(goal, merit):
                    combos.append((place, gid, mid))
    return combos


@dataclass
class StoryParams:
    place: str
    goal: str
    merit: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "badge": [("What is a merit badge?", "A merit badge is a small badge that shows someone learned a skill or finished a task.")],
    "certificate": [("What is a certificate?", "A certificate is a paper that says someone did a good job.")],
    "star": [("What is a gold star?", "A gold star is a shiny sticker people use to show praise or success.")],
    "presentation": [("What is a presentation?", "A presentation is when someone tells or shows other people what they learned or made.")],
    "cleanup": [("What does cleanup mean?", "Cleanup means putting things back in order and making a space neat again.")],
    "apology": [("What is an apology?", "An apology is when someone says sorry after making a mistake.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    teen, goal, merit = f["teen"], f["goal"], f["merit"]
    return [
        f'Write a funny story for a child about a teenager who wants {merit.phrase} and has to {goal.verb}.',
        f"Tell a comedy story where {teen.id} keeps thinking out loud inside {teen.pronoun('possessive')} own head while trying to earn merit.",
        f"Write a short, child-friendly story about {teen.id}, {goal.verb}, and finally getting {merit.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    teen, adult, goal, merit, tool = f["teen"], f["adult"], f["goal"], f["merit"], f["tool"]
    qa = [
        QAItem(
            question=f"Who is the teenager in the story trying to earn {merit.label}?",
            answer=f"The teenager is {teen.id}, and {teen.id} wants {merit.phrase}.",
        ),
        QAItem(
            question=f"What did {teen.id} want to do at {world.setting.place}?",
            answer=f"{teen.id} wanted to {goal.verb}, but {teen.pronoun('possessive')} inner monologue kept making jokes and warnings.",
        ),
        QAItem(
            question=f"Who helped {teen.id} keep going when the plan got awkward?",
            answer=f"The {adult.type}, {adult.label}, helped by suggesting {tool.prep}.",
        ),
        QAItem(
            question=f"How did {teen.id} finally earn the {merit.label}?",
            answer=f"{teen.id} earned it by calming down, trying again, and using {tool.label}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["goal"].keyword, world.facts["merit"].kind}
    out: list[QAItem] = []
    for tag in tags:
        if tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="classroom", goal="presentation", merit="badge", name="Maya", gender="girl", adult="teacher", trait="awkward"),
    StoryParams(place="hallway", goal="cleanup", merit="certificate", name="Noah", gender="boy", adult="teacher", trait="earnest"),
    StoryParams(place="library", goal="apology", merit="star", name="Zara", gender="girl", adult="librarian", trait="dramatic"),
]


ASP_RULES = r"""
goal_support(G) :- goal(G).
merit(M) :- merit_item(M).
place(P) :- setting(P).
compatible(P,G,M) :- affords(P,G), merit_item(M), needs_help(G,M).

needs_help(presentation,badge).
needs_help(presentation,certificate).
needs_help(presentation,star).
needs_help(cleanup,badge).
needs_help(cleanup,certificate).
needs_help(cleanup,star).
needs_help(apology,badge).
needs_help(apology,certificate).
needs_help(apology,star).

affords(classroom,presentation). affords(classroom,cleanup). affords(classroom,apology).
affords(hallway,presentation). affords(hallway,cleanup). affords(hallway,apology).
affords(library,presentation). affords(library,cleanup). affords(library,apology).

setting(classroom). setting(hallway). setting(library).
goal(presentation). goal(cleanup). goal(apology).
merit_item(badge). merit_item(certificate). merit_item(star).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for g in sorted(s.affords):
            lines.append(asp.fact("affords", p, g))
    for g in GOALS:
        lines.append(asp.fact("goal", g))
    for m in MERITS:
        lines.append(asp.fact("merit_item", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: a teenager, merit, and an inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--merit", choices=MERITS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and args.merit:
        goal, merit = GOALS[args.goal], MERITS[args.merit]
        if not (goal_needs_support(goal, merit) and select_tool(goal, merit)):
            raise StoryError("No reasonable comedy fix exists for that goal and merit item.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.goal is None or c[1] == args.goal)
              and (args.merit is None or c[2] == args.merit)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, goal, merit = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(TEEN_NAMES)
    adult = args.adult or rng.choice(ADULTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal, merit=merit, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], GOALS[params.goal], MERITS[params.merit], params.name, params.gender, params.adult, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.goal} at {p.place} (merit: {p.merit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
