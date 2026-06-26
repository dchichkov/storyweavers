#!/usr/bin/env python3
"""
siren_problem_solving_suspense_rhyme_heartwarming.py

A small storyworld about a child, a siren, and a gentle rescue.
The world is built around problem solving, suspense, rhyme, and a heartwarming ending.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
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
    foggy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    name: str
    danger: str
    clue: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: str = ""

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.zone = self.zone
        return w


def _r_siren(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("siren_on"):
        return out
    for c in world.characters():
        if c.memes.get("worry", 0.0) >= THRESHOLD:
            sig = ("siren_fear", c.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            c.memes["focus"] = c.memes.get("focus", 0.0) + 1
            out.append(f"The siren kept everyone alert.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    kid = world.facts.get("child")
    prob = world.facts.get("problem")
    if not kid or not prob:
        return out
    child = world.get(kid.id)
    if child.memes.get("planning", 0.0) < THRESHOLD:
        return out
    tool = world.facts.get("tool")
    if tool and tool.id not in world.fired:
        pass
    if child.meters.get("helped", 0.0) >= THRESHOLD:
        return out
    return out


CAUSAL_RULES = [_r_siren]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, problem: Problem) -> str:
    if setting.foggy:
        return f"The air was soft with fog, and {setting.place} felt quiet except for the siren."
    return f"{setting.place.capitalize()} looked calm, but the siren could still cut through the air."


def choose_tool(problem: Problem, tools: list[Tool]) -> Optional[Tool]:
    for tool in tools:
        if problem.id in tool.helps and problem.zone in tool.covers:
            return tool
    return None


def predict_outcome(world: World, child: Entity, problem: Problem, tool: Tool) -> bool:
    sim = world.copy()
    sim.facts["siren_on"] = True
    child2 = sim.get(child.id)
    child2.memes["planning"] = 1
    child2.meters["helped"] = 1
    return problem.id in tool.helps and problem.zone in tool.covers


def tell(setting: Setting, problem: Problem, tool: Tool, hero_name: str, hero_type: str,
         guardian_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "kind"]))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, label="the grown-up"))
    rescued = world.add(Entity(id="Rescued", kind="thing", type=problem.name, label=problem.name,
                               phrase=problem.name, owner=child.id, caretaker=guardian.id))
    tool_ent = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label,
                                phrase=tool.phrase, owner=guardian.id))
    world.facts.update(child=child, guardian=guardian, rescued=rescued, problem=problem,
                       tool=tool_ent, setting=setting, siren_on=True)

    world.say(f"{child.id} was a little {hero_type} who loved the safe, bright edge of {setting.place}.")
    world.say(f"One day, a siren sang out: {problem.clue}.")
    world.say(setting_detail(setting, problem))
    world.say(f"{child.id} listened hard and whispered, 'What is that sound, so near and so grand?'")
    world.say(f"{guardian.label_word if hasattr(guardian, 'label_word') else 'the grown-up'} held a warm hand and said, "
              f"'There is trouble nearby; let us be calm and try to help.'")

    world.para()
    world.say(f"{child.id} spotted {problem.name} {problem.danger} near the {problem.zone}.")
    world.say(f"The siren gave the night a hush-hush hush, and the fog made every shadow stretch.")
    world.say(f"{child.id} felt a small pinch of worry, but {child.pronoun()} did not run away.")
    world.say(f"Instead, {child.id} looked at {tool.label} and thought, '{tool.phrase} can help.'")
    world.say(f"{child.id}'s {guardian.type} nodded. {tool.prep}.")
    child.memes["planning"] = 1
    child.meters["helped"] = 1

    world.para()
    if not predict_outcome(world, child, problem, tool):
        raise StoryError("The chosen tool does not solve this problem in a believable way.")
    world.say(f"Together they used the {tool.label} to reach the {problem.name}.")
    world.say(f"Slowly, softly, surely, they followed the clue while the siren stayed in the air.")
    world.say(f"{child.id} said, 'Near the pier, clear and dear; we help with heart, not fear.'")
    world.say(f"At last, the little {problem.name} was safe.")
    world.say(f"{tool.tail}, and the worry in the air grew lighter.")

    world.para()
    child.memes["joy"] = 1
    child.memes["love"] = 1
    world.say(f"{child.id} smiled as {problem.name} curled up warm and still.")
    world.say(f"The siren was quiet now, and the fog felt less cold.")
    world.say(f"{child.id} and {guardian.label if guardian.label else 'the grown-up'} went home side by side, "
              f"happy that a small, brave plan had become a big, kind win.")
    return world


SETTINGS = {
    "harbor": Setting(place="the harbor", foggy=True, affords={"kitten", "duckling", "boat"}),
    "pier": Setting(place="the pier", foggy=True, affords={"kitten", "duckling", "boat"}),
    "lighthouse": Setting(place="the lighthouse stairs", foggy=True, affords={"boat", "duckling"}),
}

PROBLEMS = {
    "kitten": Problem(
        id="kitten",
        name="kitten",
        danger="stuck on a wobbling plank",
        clue="a tiny mew from the dock",
        zone="plank",
        keyword="kitten",
        tags={"animal", "help", "siren"},
    ),
    "duckling": Problem(
        id="duckling",
        name="duckling",
        danger="paddling in a cold puddle near the edge",
        clue="a peep-peep from the waterline",
        zone="waterline",
        keyword="duckling",
        tags={"animal", "help", "siren"},
    ),
    "boat": Problem(
        id="boat",
        name="small boat",
        danger="drifting toward the rocks",
        clue="a creak from the ropes",
        zone="rocks",
        keyword="boat",
        tags={"boat", "help", "siren"},
    ),
}

TOOLS = [
    Tool(id="rope", label="rope", phrase="A steady rope reaches farther than a scared hand.",
         helps={"kitten", "duckling", "boat"}, covers={"plank", "waterline", "rocks"},
         prep="They tied the rope to the rail and leaned together.",
         tail="They coiled the rope back up when the little one was safe"),
    Tool(id="lantern", label="lantern", phrase="A lantern makes the fog less tricky.",
         helps={"kitten", "boat"}, covers={"plank", "rocks"},
         prep="They lit the lantern so the fog could not hide the way.",
         tail="The lantern glowed like a little moon in their hands"),
    Tool(id="net", label="net", phrase="A net can scoop gently without a rough grab.",
         helps={"duckling", "kitten"}, covers={"waterline", "plank"},
         prep="They held the net low and moved as softly as sleep.",
         tail="The net came back empty and tidy, with the small one safe"),
]

GIRL_NAMES = ["Maya", "Lena", "Iris", "Nora", "Zoe", "Ruby"]
BOY_NAMES = ["Theo", "Milo", "Ezra", "Noah", "Finn", "Leo"]
TRAITS = ["brave", "gentle", "curious", "steadfast"]


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prob_id in setting.affords:
            prob = PROBLEMS[prob_id]
            for tool in TOOLS:
                if prob.id in tool.helps and prob.zone in tool.covers:
                    out.append((place, prob_id, tool.id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, g, p, t = f["child"], f["guardian"], f["problem"], f["tool"]
    return [
        f'Write a warm, suspenseful story for a young child that includes the word "siren".',
        f"Tell a heartwarming rescue story about {c.id} and {g.type} at {world.setting.place} with {p.name} and {t.label}.",
        f"Write a short rhyming story where a siren sounds, a problem is solved, and everyone feels safer by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, guardian, problem, tool = f["child"], f["guardian"], f["problem"], f["tool"]
    qa = [
        QAItem(
            question=f"What did {child.id} hear first at {world.setting.place}?",
            answer=f"{child.id} heard a siren first, and the sound meant something nearby needed help.",
        ),
        QAItem(
            question=f"What was the problem near the {problem.zone}?",
            answer=f"A {problem.name} was {problem.danger}. That is why the siren sounded so urgent.",
        ),
        QAItem(
            question=f"How did {child.id} and {guardian.label if guardian.label else 'the grown-up'} solve the problem?",
            answer=f"They used the {tool.label} carefully and worked together until the {problem.name} was safe.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and proud because a small brave plan turned into a kind rescue.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a siren?",
            answer="A siren is a loud warning sound that tells people to pay attention because there may be danger or an emergency nearby.",
        ),
        QAItem(
            question="Why can fog be tricky?",
            answer="Fog can be tricky because it makes it hard to see far away, so people have to move slowly and carefully.",
        ),
        QAItem(
            question="Why do helpers use tools like ropes or lanterns?",
            answer="Helpers use tools like ropes or lanterns because the tools make hard jobs safer and easier to do.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", problem="kitten", tool="rope", name="Maya", gender="girl", guardian="mother", trait="gentle"),
    StoryParams(place="pier", problem="duckling", tool="net", name="Theo", gender="boy", guardian="father", trait="brave"),
    StoryParams(place="lighthouse", problem="boat", tool="lantern", name="Nora", gender="girl", guardian="grandmother", trait="curious"),
]


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: a {tool.label} does not safely solve a {problem.name} problem in this world.)"


def explain_gender(problem_id: str, gender: str) -> str:
    return f"(No story: the requested gender does not fit the sampled child for {problem_id}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming siren rescue storyworld with rhyme and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father", "grandmother", "grandfather"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        prob = PROBLEMS[args.problem]
        tool = next(t for t in TOOLS if t.id == args.tool)
        if not (prob.id in tool.helps and prob.zone in tool.covers):
            raise StoryError(explain_rejection(prob, tool))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father", "grandmother"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, gender=gender, guardian=guardian, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], next(t for t in TOOLS if t.id == params.tool),
                 params.name, params.gender, params.guardian)
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


ASP_RULES = r"""
valid_combo(Place, Problem, Tool) :- affords(Place, Problem), tool(Tool), helps(Tool, Problem), covers(Tool, Zone), zone_of(Problem, Zone).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.foggy:
            lines.append(asp.fact("foggy", place))
        for p in sorted(setting.affords):
            lines.append(asp.fact("affords", place, p))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("zone_of", pid, prob.zone))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for p in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, p))
        for z in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
