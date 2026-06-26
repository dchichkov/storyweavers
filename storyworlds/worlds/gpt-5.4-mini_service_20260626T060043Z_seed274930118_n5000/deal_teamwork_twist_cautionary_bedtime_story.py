#!/usr/bin/env python3
"""
A standalone storyworld for a bedtime-style tale about a deal, teamwork,
a twist, and a gentle cautionary ending.

Premise:
- A child wants one last small adventure before bed.
- A parent worries because the night is already late and a small mistake could
  make bedtime harder.
- A deal is offered: if the child helps fix the problem with teamwork, the
  child may enjoy a calm, cozy ending.

This world models:
- physical state with meters: tiredness, mess, progress, calm, caution, trust
- emotional state with memes: worry, hope, pride, relief, patience
- a concrete twist: the helpful thing the child expects is not enough on its own
- a teamwork resolution: two characters cooperate to solve the problem
- a cautionary lesson: rushing or sneaking ahead makes bedtime harder

The prose is authored from the simulated state, not a frozen template.
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
    kind: str = "character"
    type: str = "child"
    label: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["tired", "mess", "progress", "calm", "caution", "trust"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "hope", "pride", "relief", "patience", "surprise"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap_pronoun(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()


@dataclass
class Setting:
    place: str
    quiet: bool = True
    cozy: bool = True
    bedtime_ready: bool = True
    details: str = ""


@dataclass
class Problem:
    id: str
    label: str
    concern: str
    twist: str
    caution: str
    needs_teamwork: bool = True


@dataclass
class Deal:
    id: str
    offer: str
    promise: str
    after: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.problem_active: bool = False
        self.twist_seen: bool = False
        self.deal_made: bool = False
        self.resolved: bool = False

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.problem_active = self.problem_active
        w.twist_seen = self.twist_seen
        w.deal_made = self.deal_made
        w.resolved = self.resolved
        return w


def _activate_problem(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    problem = world.facts["problem"]
    if child.meters["tired"] >= THRESHOLD and not world.problem_active:
        world.problem_active = True
        child.memes["worry"] += 1
        out.append(
            f"{child.id} was sleepy, but the little problem about {problem.label} "
            f"kept nudging {child.pronoun('object')} awake."
        )
    return out


def _twist(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    problem = world.facts["problem"]
    if not world.problem_active or world.twist_seen:
        return out
    if child.meters["mess"] >= THRESHOLD and helper.meters["trust"] >= THRESHOLD:
        world.twist_seen = True
        child.memes["surprise"] += 1
        helper.memes["hope"] += 1
        out.append(
            f"{child.id} thought {problem.concern} was the only trouble, but the real twist "
            f"was that {helper.id} had already found a small missing piece."
        )
    return out


def _teamwork_progress(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if not world.deal_made or world.resolved:
        return out
    sig = ("teamwork", world.facts["problem"].id)
    if sig in world.fired:
        return out
    if child.meters["progress"] >= THRESHOLD and helper.meters["trust"] >= THRESHOLD:
        world.fired.add(sig)
        child.meters["calm"] += 1
        child.memes["pride"] += 1
        helper.memes["relief"] += 1
        world.resolved = True
        out.append("They worked together until the bedtime job was done.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_activate_problem, _twist, _teamwork_progress):
            lines = rule(world)
            if lines:
                produced.extend(lines)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def do_rushing(world: World, child: Entity) -> None:
    child.meters["mess"] += 1
    child.meters["tired"] += 1
    child.memes["worry"] += 1
    child.meters["caution"] += 1
    world.say(
        f"{child.id} tried to hurry ahead, and that only made the room a little messier."
    )
    propagate(world, narrate=True)


def make_deal(world: World, child: Entity, helper: Entity, deal: Deal) -> None:
    world.deal_made = True
    child.memes["hope"] += 1
    helper.memes["patience"] += 1
    helper.meters["trust"] += 1
    world.say(
        f'"{deal.offer}," {helper.id} said. "{deal.promise}"'
    )
    world.say(
        f"{child.id} nodded, because the deal sounded fair and calm."
    )


def team_fix(world: World, child: Entity, helper: Entity, problem: Problem, deal: Deal) -> None:
    child.meters["progress"] += 1
    helper.meters["trust"] += 1
    world.say(
        f"{child.id} picked up one side, and {helper.id} held the other side steady."
    )
    if problem.needs_teamwork:
        world.say(
            f"That was the only way to fix {problem.label}, because one pair of hands was not quite enough."
        )
    propagate(world, narrate=True)


def close_story(world: World, child: Entity, helper: Entity, problem: Problem, deal: Deal) -> None:
    child.meters["calm"] += 1
    helper.memes["relief"] += 1
    child.memes["relief"] += 1
    world.say(
        f'At last, {deal.after}. {child.id} felt warm and proud, and {helper.id} smiled with relief.'
    )
    world.say(
        f"The room grew quiet again, and bedtime could begin the gentle way."
    )


def tell(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    problem = world.facts["problem"]
    deal = world.facts["deal"]

    world.say(
        f"On a sleepy night, {child.id} was in {world.setting.place}, where everything felt soft and still."
    )
    world.say(
        f"{child.id} wanted one more tiny adventure, but {problem.label} was already making the evening tricky."
    )
    world.para()

    world.say(
        f"{child.id} began to rush, and that was the wrong choice."
    )
    do_rushing(world, child)

    world.para()
    make_deal(world, child, helper, deal)

    world.para()
    world.say(
        f"Then came the twist: {problem.twist}"
    )
    world.say(
        f"{problem.caution}"
    )

    world.para()
    team_fix(world, child, helper, problem, deal)

    world.para()
    close_story(world, child, helper, problem, deal)

    world.facts.update(child=child, helper=helper, setting=world.setting, problem=problem, deal=deal)


SETTINGS = {
    "bedroom": Setting(
        place="the bedroom",
        quiet=True,
        cozy=True,
        bedtime_ready=True,
        details="A lamp glowed softly by the bed.",
    ),
    "nursery": Setting(
        place="the nursery",
        quiet=True,
        cozy=True,
        bedtime_ready=True,
        details="A little moon sticker shone near the window.",
    ),
    "cabin": Setting(
        place="the cabin",
        quiet=True,
        cozy=True,
        bedtime_ready=True,
        details="The pine-scented air made the blankets feel extra snug.",
    ),
}

PROBLEMS = {
    "blanket": Problem(
        id="blanket",
        label="the blanket",
        concern="the blanket was half-fallen to the floor",
        twist="the blanket had snagged under the pillow instead of simply slipping down.",
        caution="A quick tug might have pulled the whole bed crooked, so they had to be careful.",
    ),
    "toy": Problem(
        id="toy",
        label="the toy basket",
        concern="the toy basket was tipped over",
        twist="the favorite toy was stuck under a tiny stack of blocks.",
        caution="If they rushed, the blocks could spill everywhere and make bedtime noisier.",
    ),
    "book": Problem(
        id="book",
        label="the bedtime book",
        concern="the bedtime book was missing",
        twist="the book had slid behind the curtain where little hands could not see it at first.",
        caution="If they guessed too fast, they might search the wrong place and wake the room more.",
    ),
}

DEALS = {
    "tidy": Deal(
        id="tidy",
        offer="If you help me fix it carefully, we'll read one short page together",
        promise="Then we can settle down and keep the room peaceful",
        after="the blanket was tucked in neatly",
        helps="reading the short page",
    ),
    "song": Deal(
        id="song",
        offer="If you help me sort it out, I'll hum your favorite song while we work",
        promise="Then the room can get sleepy again",
        after="the toy basket stood straight and tidy",
        helps="humming the favorite song",
    ),
    "search": Deal(
        id="search",
        offer="If you help me look gently, we'll find the missing thing together",
        promise="Then bedtime will be kind and calm",
        after="the bedtime book was found behind the curtain",
        helps="looking gently",
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Lila", "Theo", "Ava", "Eli", "Nora", "Finn"]
HELPER_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]
GENDERS = {"girl": {"Mia", "Lila", "Ava", "Nora"}, "boy": {"Noah", "Theo", "Eli", "Finn"}}


@dataclass
class StoryParams:
    setting: str
    problem: str
    deal: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-style storyworld about a deal, teamwork, and a cautionary twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--deal", dest="deal_id", choices=DEALS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    deal_id = args.deal_id or rng.choice(list(DEALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    names = sorted(GENDERS[gender])
    child_name = args.name or rng.choice(names)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        problem=problem,
        deal=deal_id,
        child_name=child_name,
        child_type=gender,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.problem in PROBLEMS and params.deal in DEALS


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("Invalid story parameters.")
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id="child", type=params.child_type, label=params.child_name, role="child"))
    helper = world.add(Entity(id="helper", type=params.helper_type, label=params.helper_name, role="helper"))
    problem = PROBLEMS[params.problem]
    deal = DEALS[params.deal]
    world.facts.update(problem=problem, deal=deal)

    child.meters["tired"] = 1.0
    child.meters["mess"] = 0.5
    child.memes["hope"] = 0.5
    helper.meters["trust"] = 0.5
    helper.memes["patience"] = 0.5

    tell(world)

    prompts = [
        f"Write a calm bedtime story about {params.child_name} making a deal to solve {problem.label} with teamwork.",
        f"Tell a child-sized story where a small twist changes the plan, but the ending stays gentle.",
        f"Create a bedtime story with a cautious problem, a fair deal, and two characters helping each other.",
    ]

    story_qa = [
        QAItem(
            question=f"What deal did {params.child_name} make before bedtime?",
            answer=f"{params.child_name} agreed to help carefully, and in return they would get a calm, cozy reward before sleep.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {problem.twist}",
        ),
        QAItem(
            question="How did the characters solve the problem?",
            answer=f"They solved it with teamwork: {params.child_name} and {params.helper_name} both did their part, and the room became peaceful again.",
        ),
        QAItem(
            question="Why was the story cautionary?",
            answer=f"It showed that rushing could make bedtime harder, so the safer choice was to slow down and work carefully.",
        ),
    ]

    world_qa = [
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because two people can share the job, use different strengths, and finish safely and kindly.",
        ),
        QAItem(
            question="What does a bedtime story usually feel like?",
            answer="A bedtime story usually feels soft, quiet, and comforting, with a gentle ending that helps the listener rest.",
        ),
        QAItem(
            question="Why should you be careful at bedtime?",
            answer="Being careful at bedtime helps keep the room calm, avoids extra mess or noise, and makes it easier to fall asleep.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


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
    lines.append(f"  problem_active={world.problem_active}")
    lines.append(f"  twist_seen={world.twist_seen}")
    lines.append(f"  deal_made={world.deal_made}")
    lines.append(f"  resolved={world.resolved}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when it has a setting, a problem, and a deal.
valid_story(S,P,D) :- setting(S), problem(P), deal(D).

% The problem needs teamwork when it is marked teamwork_required.
needs_teamwork(P) :- problem(P), teamwork_required(P).

% A cautious story has a twist and a warning.
cautionary_story(P) :- problem(P), caution(P).

% A deal belongs in the story when it offers a calm reward after help.
deal_story(D) :- deal(D), after_help(D).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROBLEMS.values():
        lines.append(asp.fact("problem", p.id))
        lines.append(asp.fact("twist", p.id))
        lines.append(asp.fact("caution", p.id))
        if p.needs_teamwork:
            lines.append(asp.fact("teamwork_required", p.id))
    for d in DEALS.values():
        lines.append(asp.fact("deal", d.id))
        lines.append(asp.fact("after_help", d.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    asp_set = sorted(set(asp.atoms(model, "valid_story")))
    py_set = sorted((s, p, d) for s in SETTINGS for p in PROBLEMS for d in DEALS)
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} stories).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP only:", sorted(set(asp_set) - set(py_set)))
    print("Python only:", sorted(set(py_set) - set(asp_set)))
    return 1


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("bedroom", "blanket", "tidy", "Mia", "girl", "Mom", "mother"),
        StoryParams("nursery", "toy", "song", "Noah", "boy", "Dad", "father"),
        StoryParams("cabin", "book", "search", "Ava", "girl", "Grandma", "grandmother"),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid stories")
        for t in vals:
            print(*t)
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
            header = f"### {p.child_name}: {p.problem} / {p.deal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
