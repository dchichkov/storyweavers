#!/usr/bin/env python3
"""
A fairy-tale storyworld about a misunderstanding, a problem solved with a pact,
and a moral value learned at the end.

The seed words are woven into the world:
- outer: the outer gate / outer garden
- hij: a tiny fox-like trickster whose name is Hij
- pact: a promise-scroll that can be sealed
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
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
    outer: str
    inner: str
    mood: str = "fairy-tale"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    name: str
    symptom: str
    cause: str
    value: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pact:
    id: str
    label: str
    phrase: str
    seal_word: str
    helps: set[str] = field(default_factory=set)
    moral: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("misunderstanding", 0.0) < THRESHOLD:
            continue
        sig = ("misunderstanding", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{hero.id} felt lost in a cloud of wrong ideas.")
    return out


def _r_problem_pressure(world: World) -> list[str]:
    out: list[str] = []
    for p in world.facts.get("problems", []):
        if p["severity"] < THRESHOLD:
            continue
        sig = ("problem_pressure", p["id"])
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The trouble around {p['name']} kept tugging at the day.")
    return out


def _r_pact_resolution(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("pact_signed"):
        return out
    sig = ("pact_resolution",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The pact made a clear path where confusion had been.")
    return out


CAUSAL_RULES = [
    _r_misunderstanding,
    _r_problem_pressure,
    _r_pact_resolution,
]


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


def reasonableness_gate(setting: Setting, problem: Problem, pact: Pact) -> bool:
    return problem.id in pact.helps and problem.value == pact.moral


def predict_resolution(world: World, hero: Entity, problem: Problem, pact: Pact) -> dict:
    sim = world.copy()
    sim.facts["pact_signed"] = True
    hero2 = sim.get(hero.id)
    hero2.memes["misunderstanding"] = 0.0
    return {"solved": reasonableness_gate(sim.setting, problem, pact)}


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Once upon a time, {hero.id} was a little {hero.traits[0]} {hero.type} "
        f"who loved the quiet light beyond the {world.setting.outer}."
    )


def show_setting(world: World) -> None:
    world.say(
        f"Inside {world.setting.place}, the {world.setting.inner} smelled of honey and old stories, "
        f"while the {world.setting.outer} gate stood bright in the moonlight."
    )


def set_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["misunderstanding"] = 1.0
    world.facts["problems"] = [{"id": problem.id, "name": problem.name, "severity": 1.0}]
    world.say(
        f"But one day, a misunderstanding rose: {problem.name} seemed to mean one thing, "
        f"when it truly meant another."
    )
    world.say(f"The trouble was this: {problem.symptom}")


def warn(world: World, elder: Entity, hero: Entity, problem: Problem) -> None:
    world.say(
        f'"Careful," said {elder.id}, "for the wrong thought can make even a small door feel locked."'
    )


def complicate(world: World, trickster: Entity, hero: Entity, problem: Problem) -> None:
    trickster.memes["mischief"] = 1.0
    world.say(
        f"Then Hij came by with a shiny grin and mixed the signs by the outer wall, "
        f"making the misunderstanding grow even bigger."
    )


def solve(world: World, hero: Entity, elder: Entity, pact: Pact, problem: Problem) -> None:
    world.say(
        f"{hero.id} listened, breathed slowly, and asked {elder.id} to make a pact."
    )
    world.say(
        f'Together they sealed the {pact.label} with the word "{pact.seal_word}", '
        f'and the promise said they would check the truth before choosing a fear.'
    )
    world.facts["pact_signed"] = True
    hero.memes["misunderstanding"] = 0.0
    world.facts["problem_fixed"] = True
    propagate(world, narrate=True)
    world.say(
        f"Once they had spoken plainly, the problem softened, and the path from the outer gate "
        f"to the inner hall opened like a smile."
    )


def moral(world: World, pact: Pact, hero: Entity) -> None:
    world.say(
        f"In the end, {hero.id} learned {pact.moral}: when people speak kindly and check the truth, "
        f"a misunderstanding can become understanding."
    )


SETTINGS = {
    "castle": Setting(place="the old castle", outer="outer", inner="great hall", affords={"talk", "pact"}),
    "garden": Setting(place="the lantern garden", outer="outer", inner="flower arbor", affords={"talk", "pact"}),
    "tower": Setting(place="the round tower", outer="outer", inner="stone chamber", affords={"talk", "pact"}),
}

PROBLEMS = {
    "gate_sign": Problem(
        id="gate_sign",
        name="the sign at the gate",
        symptom="the sign pointed inward when it should have pointed outward",
        cause="a gust of wind and a hurried hand",
        value="truth matters",
        fix_hint="turn the sign, then speak plainly",
        tags={"misunderstanding", "outer"},
    ),
    "echo_message": Problem(
        id="echo_message",
        name="the echo in the hall",
        symptom="the echo repeated half a sentence and made it sound like a command",
        cause="stone walls and a worried ear",
        value="listen carefully",
        fix_hint="repeat the message slowly",
        tags={"misunderstanding"},
    ),
    "missing_key": Problem(
        id="missing_key",
        name="the missing key",
        symptom="everyone thought the key was stolen, but it had been tucked into a blue bowl",
        cause="nobody checked the shelf",
        value="check before you blame",
        fix_hint="look in the blue bowl",
        tags={"problem solving"},
    ),
}

PACTS = {
    "truth_pact": Pact(
        id="truth_pact",
        label="truth pact",
        phrase="a promise-scroll",
        seal_word="true",
        helps={"gate_sign"},
        moral="truth matters",
    ),
    "careful_listening": Pact(
        id="careful_listening",
        label="listening pact",
        phrase="a silver ribbon oath",
        seal_word="clear",
        helps={"echo_message"},
        moral="listen carefully",
    ),
    "check_first": Pact(
        id="check_first",
        label="checking pact",
        phrase="a little wax-sealed promise",
        seal_word="wise",
        helps={"missing_key"},
        moral="check before you blame",
    ),
}

HERO_NAMES = ["Elara", "Mina", "Nori", "Tilda", "Rowan", "Pippa"]
ELDER_NAMES = ["Grandmother Fern", "Old King Bram", "Aunt Willow", "The Baker"]
TRICKSTER_NAMES = ["Hij"]

MORAL_ORDER = ["truth matters", "listen carefully", "check before you blame"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    pact: str
    hero: str
    elder: str
    trickster: str = "Hij"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about misunderstanding, problem solving, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--pact", choices=PACTS)
    ap.add_argument("--hero")
    ap.add_argument("--elder")
    ap.add_argument("--trickster", choices=TRICKSTER_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for xid, pact in PACTS.items():
                if reasonableness_gate(setting, problem, pact):
                    combos.append((sid, pid, xid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.pact:
        if not reasonableness_gate(SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values())),
                                   PROBLEMS[args.problem], PACTS[args.pact]):
            raise StoryError("No story: that pact does not really solve that problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.pact is None or c[2] == args.pact)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, problem, pact = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    trickster = args.trickster or "Hij"
    return StoryParams(setting=setting, problem=problem, pact=pact, hero=hero, elder=elder, trickster=trickster)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    problem = PROBLEMS[params.problem]
    pact = PACTS[params.pact]
    world = World(setting)

    hero = world.add(Entity(id=params.hero, kind="character", type="girl", traits=["curious", "gentle"]))
    elder = world.add(Entity(id=params.elder, kind="character", type="woman", traits=["wise"]))
    trickster = world.add(Entity(id=params.trickster, kind="character", type="thing", traits=["tricky"]))
    world.facts.update(problem=problem, pact=pact, hero=hero, elder=elder, trickster=trickster)

    introduce(world, hero)
    show_setting(world)
    world.para()
    set_problem(world, hero, problem)
    warn(world, elder, hero, problem)
    complicate(world, trickster, hero, problem)
    world.para()
    solve(world, hero, elder, pact, problem)
    moral(world, pact, hero)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale for a young child about a misunderstanding at the outer gate, using the word "outer".',
        f"Tell a gentle story where {f['hero'].id} and {f['elder'].id} solve a problem with a pact and learn a moral value.",
        f'Write a short story that includes Hij, a pact, and a problem solved by speaking the truth.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    trickster: Entity = f["trickster"]
    problem: Problem = f["problem"]
    pact: Pact = f["pact"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who lived in a fairy-tale place and learned how to solve a misunderstanding.",
        ),
        QAItem(
            question=f"What problem caused the misunderstanding?",
            answer=f"{problem.name} caused the misunderstanding because {problem.symptom}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think clearly?",
            answer=f"{elder.id} helped {hero.id} think clearly, and Hij made the confusion worse before they fixed it.",
        ),
        QAItem(
            question=f"What did {hero.id} and {elder.id} make to solve the trouble?",
            answer=f"They made {pact.phrase} called the {pact.label}, and they sealed it with the word '{pact.seal_word}'.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} learn?",
            answer=f"{pact.moral.capitalize()} was the moral value they learned at the end.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    pact: Pact = f["pact"]
    out = [
        QAItem(
            question="What is a pact?",
            answer="A pact is a promise or agreement that people make so they can work together and keep trust.",
        ),
        QAItem(
            question="What does a misunderstanding mean?",
            answer="A misunderstanding happens when someone gets the wrong idea about what something means.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good lesson about how to act with honesty, kindness, or care.",
        ),
    ]
    if pact.moral == "truth matters":
        out.append(QAItem(question="Why is truth helpful in a story?", answer="Truth helps because it clears away wrong ideas and lets people trust each other."))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="castle", problem="gate_sign", pact="truth_pact", hero="Elara", elder="Grandmother Fern", trickster="Hij"),
    StoryParams(setting="garden", problem="echo_message", pact="careful_listening", hero="Mina", elder="Aunt Willow", trickster="Hij"),
    StoryParams(setting="tower", problem="missing_key", pact="check_first", hero="Nori", elder="Old King Bram", trickster="Hij"),
]


ASP_RULES = r"""
problem(P) :- problem_name(P).
pact(X) :- pact_name(X).
solves(P, X) :- problem_name(P), pact_name(X), helps(X, P).
valid_story(S, P, X) :- setting(S), problem_name(P), pact_name(X), solves(P, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_name", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
        lines.append(asp.fact("moral", pid, p.value))
    for xid, x in PACTS.items():
        lines.append(asp.fact("pact_name", xid))
        lines.append(asp.fact("helps", xid, *sorted(x.helps)) if False else "")
        for pid in sorted(x.helps):
            lines.append(asp.fact("helps", xid, pid))
        lines.append(asp.fact("pact_moral", xid, x.moral))
    return "\n".join(l for l in lines if l)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solves/2.\n"))
    return sorted(set(asp.atoms(model, "solves")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, x) for _, p, x in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solves/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solves/2.\n"))
        print(sorted(set(asp.atoms(model, "solves"))))
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
            header = f"### {p.hero}: {p.problem} with {p.pact}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
