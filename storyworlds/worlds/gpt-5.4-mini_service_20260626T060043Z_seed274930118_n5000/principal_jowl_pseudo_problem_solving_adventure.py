#!/usr/bin/env python3
"""
storyworlds/worlds/principal_jowl_pseudo_problem_solving_adventure.py
=====================================================================

A small story world about a child, a school problem, and an adventurous
problem-solving turn.

Premise:
A child brings a strange pseudo-map to school, but a hallway door jams and the
principal notices. The child must solve the problem, face a stern look, and turn
the day into a tiny adventure.

World model:
- typed entities carry physical meters and emotional memes
- the story is driven by a stateful problem, a failed attempt, and a fix
- the ending image proves what changed

Seed words used in the domain:
- principal
- jowl
- pseudo

Style:
- adventure
- child-facing
- concrete and causal
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    principal_kind: str
    problem: str
    clue: str
    tool: str
    seed: Optional[int] = None


PLACES = {
    "school": "the school",
    "library": "the library",
    "museum": "the museum",
    "playground": "the playground",
}

NAMES_GIRL = ["Mia", "Lina", "Zoe", "Ava", "Nora"]
NAMES_BOY = ["Leo", "Finn", "Max", "Theo", "Ben"]
PROBLEMS = {
    "jammed_door": {
        "label": "jammed door",
        "verb": "open the stuck door",
        "rush": "push hard at the door",
        "risk": "the hallway would stay blocked",
        "fix": "find the loose key under the mat",
        "resolution": "The door swung open with a tired creak",
        "signal": "stuck",
    },
    "lost_map": {
        "label": "lost pseudo-map",
        "verb": "find the right room",
        "rush": "dash the wrong way",
        "risk": "they would end up in circles",
        "fix": "follow the chalk arrows",
        "resolution": "The chalk arrows led them straight ahead",
        "signal": "lost",
    },
    "spilled_bins": {
        "label": "spilled bins",
        "verb": "sort the fallen papers",
        "rush": "grab papers from the floor",
        "risk": "the notes would scatter farther",
        "fix": "use a flat tray",
        "resolution": "The tray held the papers in one neat stack",
        "signal": "messy",
    },
}

TOOLS = {
    "pseudo_map": {
        "label": "a pseudo-map",
        "phrase": "a hand-drawn pseudo-map with wobbly arrows",
        "help": "the fake-looking map turned out to be a clue",
    },
    "chalk": {
        "label": "chalk",
        "phrase": "a piece of chalk",
        "help": "the chalk could mark a safe path",
    },
    "tray": {
        "label": "a tray",
        "phrase": "a flat tray",
        "help": "the tray could carry things without dropping them",
    },
}

PRINCIPALS = {
    "kind": {
        "type": "principal",
        "label": "the principal",
        "phrase": "a kind principal with bright eyes",
        "jowl": "soft",
        "reaction": "gave a calm nod",
        "style": "kindly",
    },
    "stern": {
        "type": "principal",
        "label": "the principal",
        "phrase": "a stern principal with a sharp jowl",
        "jowl": "sharp",
        "reaction": "folded their arms and looked serious",
        "style": "serious",
    },
}

GENDER_NAMES = {"girl": NAMES_GIRL, "boy": NAMES_BOY}


def _room_line(place: str, problem: str) -> str:
    if problem == "jammed_door":
        return f"{place.capitalize()} had one narrow hall where a door could jam if it was pushed the wrong way."
    if problem == "lost_map":
        return f"{place.capitalize()} had twisting corridors that made even a good route look strange."
    return f"{place.capitalize()} had tables and shelves where papers could spill fast if nobody stayed careful."


def predict_fix(world: World, problem_id: str) -> bool:
    return problem_id in PROBLEMS


def solve_problem(world: World, child: Entity, principal: Entity, problem_id: str, tool_id: str) -> None:
    problem = PROBLEMS[problem_id]
    tool = TOOLS[tool_id]

    child.memes["worry"] += 1
    world.say(
        f"{child.id} noticed {problem['label']} and held up {tool['label']}. "
        f"{tool['help'].capitalize()}."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to {problem['verb']}, but {problem['risk']}."
    )
    world.say(
        f"Then {principal.label} watched with a careful jowl and {principal.memes['mood_text']}."
    )

    if problem_id == "jammed_door" and tool_id == "pseudo_map":
        world.say(f"The pseudo-map pointed to the tiny key shelf by the wall.")
    elif problem_id == "lost_map" and tool_id == "chalk":
        world.say(f"{child.id} used the chalk to draw a line that the eyes could trust.")
    elif problem_id == "spilled_bins" and tool_id == "tray":
        world.say(f"{child.id} slid the papers onto the tray before they blew away.")

    child.memes["hope"] += 1
    principal.memes["approval"] += 1
    child.memes["worry"] = 0
    child.memes["pride"] += 1
    world.say(problem["resolution"] + f", and {child.id} smiled at {principal.pronoun('object')}.")


def tell(place: str, name: str, gender: str, principal_kind: str, problem_id: str, tool_id: str) -> World:
    world = World(place=PLACES[place])
    principal_cfg = PRINCIPALS[principal_kind]
    problem = PROBLEMS[problem_id]
    tool = TOOLS[tool_id]

    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        phrase=f"a small {gender} named {name}",
        meters={"steps": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "pride": 0.0},
    ))
    principal = world.add(Entity(
        id="principal",
        kind="character",
        type=principal_cfg["type"],
        label=principal_cfg["label"],
        phrase=principal_cfg["phrase"],
        meters={"watch": 0.0},
        memes={"approval": 0.0, "mood_text": 0.0},
    ))
    principal.memes["mood_text"] = 1.0

    clue = world.add(Entity(
        id="clue",
        type="thing",
        label=tool["label"],
        phrase=tool["phrase"],
        owner=child.id,
    ))
    obstacle = world.add(Entity(
        id="problem",
        type="thing",
        label=problem["label"],
        phrase=problem["label"],
        owner=None,
    ))

    world.say(f"{child.id} was a curious child who loved a small adventure.")
    world.say(f"{child.id} had {clue.phrase}, and it felt like a secret clue for the day.")
    world.say(f"At {world.place}, {problem['label']} waited in the way.")
    world.say(_room_line(world.place, problem_id))

    world.para()
    world.say(f"{child.id} stepped closer to see what was wrong.")
    world.say(f"{child.id} felt brave enough to try a fix, even if the first idea might fail.")
    solve_problem(world, child, principal, problem_id, tool_id)

    world.facts.update(
        child=child,
        principal=principal,
        problem=obstacle,
        tool=clue,
        problem_id=problem_id,
        tool_id=tool_id,
        principal_kind=principal_kind,
        place=place,
        gender=gender,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child that includes the word "pseudo".',
        f"Tell a story where {f['child'].id} meets a {f['principal_kind']} principal and solves a {f['problem_id']} problem with a clue.",
        f"Write a gentle school adventure about {f['child'].id}, a principal, and a smart fix to a tricky problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    principal: Entity = f["principal"]
    problem_id = f["problem_id"]
    tool: Entity = f["tool"]
    problem = PROBLEMS[problem_id]
    place = f["place"]
    qa = [
        QAItem(
            question=f"What problem did {child.id} notice at {PLACES[place]}?",
            answer=f"{child.id} noticed {problem['label']} at {PLACES[place]}. It made the day tricky because {problem['risk']}.",
        ),
        QAItem(
            question=f"What did {child.id} use to help solve the problem?",
            answer=f"{child.id} used {tool.phrase}. It worked as a clue and helped the child choose a safer way forward.",
        ),
        QAItem(
            question=f"How did the principal react when the problem got solved?",
            answer=f"The principal watched carefully, then {principal_cfg_phrase(f['principal_kind'])}. At the end, the principal seemed pleased and calm.",
        ),
    ]
    if problem_id == "jammed_door":
        qa.append(QAItem(
            question=f"Why was the door a problem?",
            answer="The door was jammed, so the hallway would stay blocked until someone found the right way to open it.",
        ))
    elif problem_id == "lost_map":
        qa.append(QAItem(
            question=f"Why was the pseudo-map useful?",
            answer="The pseudo-map looked fake at first, but it still gave a clue that helped the child choose the right path.",
        ))
    else:
        qa.append(QAItem(
            question=f"What kept the papers from scattering more?",
            answer="A flat tray kept the papers together, so the child could gather them safely instead of chasing them all over the floor.",
        ))
    return qa


def principal_cfg_phrase(kind: str) -> str:
    return PRINCIPALS[kind]["reaction"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a principal?",
            answer="A principal is the adult who helps lead a school and keeps it safe and organized.",
        ),
        QAItem(
            question="What does pseudo mean in a story clue?",
            answer="Pseudo means fake or not quite real. A pseudo-map can look odd, but it may still point to a useful clue.",
        ),
        QAItem(
            question="What is a jowl?",
            answer="A jowl is the loose part of the cheek or jaw on an animal or person. In a story, it can help describe how someone looks serious or soft.",
        ),
    ]
    if f["problem_id"] == "jammed_door":
        out.append(QAItem(
            question="What makes a door jam?",
            answer="A door can jam when something blocks it or when it gets stuck and will not swing the way it should.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for problem_id in PROBLEMS:
            for tool_id in TOOLS:
                if problem_id == "jammed_door" and tool_id == "pseudo_map":
                    combos.append((place, problem_id, tool_id, "stern"))
                elif problem_id == "lost_map" and tool_id == "chalk":
                    combos.append((place, problem_id, tool_id, "kind"))
                elif problem_id == "spilled_bins" and tool_id == "tray":
                    combos.append((place, problem_id, tool_id, "kind"))
    return combos


def explain_rejection(problem_id: str, tool_id: str) -> str:
    return (
        f"(No story: {TOOLS[tool_id]['label']} does not meaningfully solve "
        f"{PROBLEMS[problem_id]['label']}. This world only tells stories when the clue "
        f"can actually fix the problem.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for p in PRINCIPALS:
        lines.append(asp.fact("principal_kind", p))
    for prob in PROBLEMS:
        lines.append(asp.fact("problem", prob))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    lines.append(asp.fact("solves", "pseudo_map", "jammed_door"))
    lines.append(asp.fact("solves", "chalk", "lost_map"))
    lines.append(asp.fact("solves", "tray", "spilled_bins"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Prob, Tool, Kind) :- place(P), problem(Prob), tool(Tool), principal_kind(Kind), solves(Tool, Prob).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: principal, jowl, pseudo, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--principal-kind", choices=PRINCIPALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
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
    filtered = []
    for place, prob, tool, kind in combos:
        if args.place and place != args.place:
            continue
        if args.problem and prob != args.problem:
            continue
        if args.tool and tool != args.tool:
            continue
        if args.principal_kind and kind != args.principal_kind:
            continue
        filtered.append((place, prob, tool, kind))
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem_id, tool_id, kind = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDER_NAMES[gender])
    return StoryParams(place=place, name=name, gender=gender, principal_kind=kind, problem=problem_id, clue=tool_id, tool=tool_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.name, params.gender, params.principal_kind, params.problem, params.tool)
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
    StoryParams(place="school", name="Mia", gender="girl", principal_kind="stern", problem="jammed_door", clue="pseudo_map", tool="pseudo_map"),
    StoryParams(place="library", name="Leo", gender="boy", principal_kind="kind", problem="lost_map", clue="chalk", tool="chalk"),
    StoryParams(place="museum", name="Nora", gender="girl", principal_kind="kind", problem="spilled_bins", clue="tray", tool="tray"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
