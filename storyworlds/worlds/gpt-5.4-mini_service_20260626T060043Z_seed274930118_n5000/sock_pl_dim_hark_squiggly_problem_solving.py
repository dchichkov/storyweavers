#!/usr/bin/env python3
"""
storyworlds/worlds/sock_pl_dim_hark_squiggly_problem_solving.py
===============================================================

A tall-tale story world about a squeaky-big problem, a clever fix, and a bit of
dialogue by the lantern light.

Seed inspiration:
- sock-pl-dim
- hark
- squiggly

The world is built around a small crew, a strange squiggly trouble, and a
problem-solving turn where talk, tools, and teamwork matter.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the barnyard"
    indoors: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    name: str
    verb: str
    symptom: str
    source: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fix_for: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barnyard": Setting(place="the barnyard", indoors=False, affordances={"hark", "squiggly"}),
    "riverbank": Setting(place="the riverbank", indoors=False, affordances={"hark", "squiggly"}),
    "workshop": Setting(place="the workshop", indoors=True, affordances={"squiggly"}),
}

TROUBLES = {
    "hark": Trouble(
        id="hark",
        name="the hark in the path",
        verb="hark at the humming ground",
        symptom="a loud, listening hush",
        source="a hidden groove in the boards",
        keyword="hark",
        tags={"sound", "listen"},
    ),
    "squiggly": Trouble(
        id="squiggly",
        name="the squiggly tangle",
        verb="untwist the squiggly trouble",
        symptom="a twisty, hopping snarl",
        source="a stubborn vine knot",
        keyword="squiggly",
        tags={"twist", "tangle"},
    ),
    "sock_pl_dim": Trouble(
        id="sock_pl_dim",
        name="the sock-pl-dim dimness",
        verb="brighten the sock-pl-dim corner",
        symptom="a dim little gloom",
        source="a covered lantern glass",
        keyword="sock-pl-dim",
        tags={"dim", "light"},
    ),
}

TOOLS = [
    Tool(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        fix_for={"sock_pl_dim"},
        prep="lift the lantern high",
        tail="kept the lantern shining over the path",
    ),
    Tool(
        id="hook",
        label="hook",
        phrase="a long shepherd's hook",
        fix_for={"squiggly"},
        prep="catch the tangle and tease it loose",
        tail="worked the hook until the squiggle came free",
    ),
    Tool(
        id="cup",
        label="cup",
        phrase="a tin cup",
        fix_for={"hark"},
        prep="tap the boards and listen close",
        tail="made the little tremble easy to hear",
    ),
    Tool(
        id="rope",
        label="rope",
        phrase="a coil of rope",
        fix_for={"squiggly", "hark"},
        prep="tie the loose ends and pull steady",
        tail="turned the snarl into a straight line",
        plural=False,
    ),
]

NAMES = ["Mabel", "Hank", "June", "Bess", "Toby", "Clara", "Eli", "Wren"]
TROTS = ["sturdy", "cheery", "bright-eyed", "good-hearted", "riverwise", "plain-spoken"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for tid in TROUBLES:
            if tid in setting.affordances:
                combos.append((place, tid))
    return combos


def explain_rejection(place: str, trouble: str) -> str:
    return (
        f"(No story: {place} doesn't fit that kind of trouble in a plausible way. "
        f"Pick a setting where the problem can actually be met and solved.)"
    )


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------

class StoryWorld(World):
    pass


def _problem_present(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"In {world.setting.place}, {hero.id} heard a {trouble.keyword} kind of hush, "
        f"the sort of hush that makes a small soul stand taller."
    )
    world.say(
        f"{hero.pronoun().capitalize()} said, \"Hark! Something is wrong, and I mean to "
        f"set it right.\""
    )


def _inspect(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    world.say(
        f"{hero.id} bent down and studied the trouble. It had {trouble.symptom}, "
        f"and its trail led from {trouble.source}."
    )
    world.say(
        f"\"If we know the source, we know the road home,\" {hero.id} said."
    )


def _select_tool(world: World, trouble: Trouble) -> Optional[Tool]:
    for tool in TOOLS:
        if trouble.id in tool.fix_for:
            return tool
    return None


def _use_tool(world: World, hero: Entity, helper: Entity, trouble: Trouble, tool: Tool) -> None:
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0.0) + 1
    world.say(
        f"\"Bring me the {tool.label},\" {hero.id} said, and {helper.id} fetched "
        f"{tool.phrase} without a fuss."
    )
    world.say(
        f"Together they chose to {tool.prep}. That was tall-tale work, with care in one hand "
        f"and patience in the other."
    )
    trouble_meter = hero.meters.setdefault(trouble.id, 0.0)
    hero.meters[trouble.id] = trouble_meter + 1
    world.facts["tool"] = tool.id
    world.facts["resolved"] = True
    world.say(
        f"{tool.tail}, and the {trouble.keyword} trouble loosened up like a knot after a kind word."
    )


def _resolve(world: World, hero: Entity, helper: Entity, trouble: Trouble) -> None:
    tool = _select_tool(world, trouble)
    if tool is None:
        raise StoryError("No reasonable tool exists for this trouble.")
    _use_tool(world, hero, helper, trouble, tool)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f"Before long, the path was clear. {hero.id} grinned from ear to ear, and "
        f"{helper.id} gave a proud little nod."
    )
    world.say(
        f"At the end of the day, the barnyard held no more squiggly riddle, no more dim corner, "
        f"and no more listening hush. Only an easy road and a bright, brave pair remained."
    )


def tell(setting: Setting, trouble: Trouble, name: str, gender: str, helper_name: str, trait: str) -> World:
    world = StoryWorld(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult", label=helper_name, traits=["helpful"]))

    world.facts.update(hero=hero, helper=helper, trouble=trouble, setting=setting)

    world.say(
        f"{name} was a little {trait} {gender} who could spot a problem from a mile away."
    )
    world.say(
        f"{helper_name} was the kind of helper who listened twice and spoke once."
    )

    world.para()
    _problem_present(world, hero, trouble)
    _inspect(world, hero, trouble)
    world.say(
        f"\"We'll need more than wishing,\" said {helper_name}. \"We'll need a plan.\""
    )

    world.para()
    _resolve(world, hero, helper, trouble)

    return world


# ---------------------------------------------------------------------------
# Params, Q&A, serialization
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    return [
        f'Write a short tall-tale story for a child where {hero.id} says "Hark!" and '
        f"solves a {trouble.keyword} problem with help.",
        f"Tell a story with dialogue in which {hero.id} and a helper face a "
        f"{trouble.name} and fix it step by step.",
        f'Write a simple problem-solving tale that includes the words "hark" and '
        f'"squiggly" in a natural way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    trouble: Trouble = f["trouble"]  # type: ignore[assignment]
    tool = next((t for t in TOOLS if t.id == f.get("tool")), None)

    qa = [
        QAItem(
            question=f"Who heard the trouble first in {world.setting.place}?",
            answer=f"{hero.id} heard it first, then called out, \"Hark!\" to get help.",
        ),
        QAItem(
            question=f"What kind of problem did {hero.id} solve?",
            answer=f"{hero.id} solved {trouble.name}, which was a {trouble.keyword} problem.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the fix?",
            answer=f"{helper.id} helped by listening, fetching tools, and working beside {hero.id}.",
        ),
    ]
    if tool:
        qa.append(
            QAItem(
                question=f"What tool helped with the {trouble.keyword} trouble?",
                answer=f"{tool.phrase} helped, because it matched the kind of trouble they faced.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with the trouble solved, the path cleared, and {hero.id} and "
                f"{helper.id} feeling proud."
            ),
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does 'hark' mean in a story?",
            answer="It is a way of saying, 'Listen carefully!'",
        ),
        QAItem(
            question="What does squiggly mean?",
            answer="Squiggly means twisty or wavy, like a line that does not stay straight.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a trouble, thinking about it, and choosing a good way to fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_combo(P, T) :- place(P), trouble(T), afford(P, T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for t in sorted(s.affordances):
            lines.append(asp.fact("afford", p, t))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print(" only in Python:", sorted(py - asp_set))
    print(" only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale problem-solving story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TROTS)
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
    if args.place and args.trouble and (args.trouble not in SETTINGS[args.place].affordances):
        raise StoryError(explain_rejection(args.place, args.trouble))

    combos = [
        (p, t) for p, t in valid_combos()
        if (args.place is None or p == args.place)
        and (args.trouble is None or t == args.trouble)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, trouble = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    trait = args.trait or rng.choice(TROTS)
    return StoryParams(place=place, trouble=trouble, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TROUBLES[params.trouble],
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, t in combos:
            print(f"  {p:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p, t in valid_combos():
            params = StoryParams(
                place=p,
                trouble=t,
                name=random.choice(NAMES),
                gender=random.choice(["girl", "boy"]),
                helper=random.choice(NAMES),
                trait=random.choice(TROTS),
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
