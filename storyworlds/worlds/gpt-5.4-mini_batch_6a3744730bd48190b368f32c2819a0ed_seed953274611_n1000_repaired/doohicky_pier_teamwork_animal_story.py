#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/doohicky_pier_teamwork_animal_story.py
======================================================================

A small standalone storyworld for a pier-side animal teamwork tale.

Premise:
- A little animal crew works together on a pier.
- A tricky doohicky gets stuck or misplaced.
- They cooperate, solve a practical problem, and end with a concrete image of the change.

The story uses a simple simulated world model with physical meters and emotional memes,
plus a tiny inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "female"}
        male = {"boy", "father", "dad", "man", "male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class AnimalKind:
    id: str
    label: str
    sound: str
    plural: str
    pronoun_type: str
    traits: list[str] = field(default_factory=list)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Doohicky:
    id: str
    label: str
    purpose: str
    stuck_text: str
    fixed_text: str
    useful: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Problem:
    id: str
    label: str
    risk: str
    mess: str
    blocks: str
    fix_need: str
    severity: int = 1
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class TeamworkMove:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail_text: str
    qa_text: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    setting: str
    animal1: str
    animal2: str
    doohicky: str
    problem: str
    move: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "pier": {
        "label": "the pier",
        "scene": "the wooden pier by the water",
        "detail": "The boards creaked, gulls called overhead, and little waves tapped the pilings.",
    }
}

ANIMALS = {
    "seal": AnimalKind("seal", "seal", "arf", "seals", "it", ["playful", "quick"]),
    "otter": AnimalKind("otter", "otter", "eep", "otters", "it", ["clever", "busy"]),
    "crab": AnimalKind("crab", "crab", "click", "crabs", "it", ["careful", "small"]),
    "duck": AnimalKind("duck", "duck", "quack", "ducks", "it", ["brave", "curious"]),
}

DOOHICKIES = {
    "rope_winch": Doohicky("rope_winch", "rope winch", "haul a little net", "the rope winch jammed", "the rope winch turned smoothly"),
    "fish_hook": Doohicky("fish_hook", "fish hook", "lift a basket", "the fish hook slipped loose", "the fish hook held steady"),
    "crate_pulley": Doohicky("crate_pulley", "crate pulley", "move a crate of apples", "the crate pulley squeaked and stuck", "the crate pulley rolled again"),
}

PROBLEMS = {
    "stuck_net": Problem("stuck_net", "stuck net", "the net could not move", "the net tangled on the pier rail", "the net blocked the way", "pull the net free together", 1),
    "fallen_basket": Problem("fallen_basket", "fallen basket", "the basket might spill", "the basket tipped near the edge", "the apples rolled toward the water", "steady the basket together", 1),
    "heavy_crate": Problem("heavy_crate", "heavy crate", "the crate was too heavy", "the crate sat too heavy for one animal", "the crate would not budge", "lift the crate together", 1),
}

MOVES = {
    "pull": TeamworkMove("pull", "pull together", 3, 2, "worked together and pulled until the jam loosened", "pulled, but the jam stayed tight", "pulled the doohicky free together"),
    "push": TeamworkMove("push", "push together", 3, 2, "worked together and pushed until it moved", "pushed, but it only wobbled", "pushed the crate into place together"),
    "steady": TeamworkMove("steady", "steady together", 3, 2, "worked together and held it steady until it settled", "held on, but it still slipped", "held the basket steady together"),
    "twist": TeamworkMove("twist", "twist together", 2, 1, "worked together and twisted the stuck part loose", "twisted, but nothing gave", "twisted the doohicky loose together"),
}

GREETINGS = [
    "The morning on the pier was bright and salty.",
    "The pier felt busy and cheerful beside the water.",
    "Gulls hopped along the rail while the tide shimmered below.",
]

CURATED = [
    StoryParams(setting="pier", animal1="seal", animal2="otter", doohicky="rope_winch", problem="stuck_net", move="pull"),
    StoryParams(setting="pier", animal1="duck", animal2="crab", doohicky="crate_pulley", problem="heavy_crate", move="push"),
    StoryParams(setting="pier", animal1="otter", animal2="duck", doohicky="fish_hook", problem="fallen_basket", move="steady"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a1 in ANIMALS:
            for a2 in ANIMALS:
                if a1 == a2:
                    continue
                for d in DOOHICKIES:
                    for p in PROBLEMS:
                        for m in MOVES:
                            if p == "stuck_net" and m in {"pull", "twist"}:
                                combos.append((s, a1, a2, d, p, m))
                            elif p == "fallen_basket" and m == "steady":
                                combos.append((s, a1, a2, d, p, m))
                            elif p == "heavy_crate" and m in {"push", "pull"}:
                                combos.append((s, a1, a2, d, p, m))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.animal1 not in ANIMALS or params.animal2 not in ANIMALS:
        raise StoryError("Unknown animal choice.")
    if params.animal1 == params.animal2:
        raise StoryError("The team needs two different animals.")
    if params.doohicky not in DOOHICKIES:
        raise StoryError("Unknown doohicky.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.move not in MOVES:
        raise StoryError("Unknown teamwork move.")
    combo = (params.setting, params.animal1, params.animal2, params.doohicky, params.problem, params.move)
    if combo not in valid_combos():
        raise StoryError("That combination does not make a reasonable teamwork story.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pier-side animal teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--doohicky", choices=DOOHICKIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _choose_two(rng: random.Random) -> tuple[str, str]:
    a1, a2 = rng.sample(list(ANIMALS), 2)
    return a1, a2


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "pier"
    a1, a2 = (args.animal1, args.animal2) if args.animal1 and args.animal2 else _choose_two(rng)
    doohicky = args.doohicky or rng.choice(list(DOOHICKIES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    move = args.move or rng.choice(list(MOVES))
    params = StoryParams(setting=setting, animal1=a1, animal2=a2, doohicky=doohicky, problem=problem, move=move)
    reasonableness_gate(params)
    return params


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for e in world.animals():
            if e.meters["teamwork"] >= THRESHOLD and e.meters["success"] < THRESHOLD and ("solve", e.id) not in world.fired:
                world.fired.add(("solve", e.id))
                e.memes["joy"] += 1
                out.append("__solve__")
                changed = True
    if narrate:
        for s in out:
            if not s.startswith("__"):
                world.say(s)
    return out


def build_world(params: StoryParams) -> World:
    world = World()
    scene = SETTINGS[params.setting]
    a1k = ANIMALS[params.animal1]
    a2k = ANIMALS[params.animal2]
    doh = DOOHICKIES[params.doohicky]
    prob = PROBLEMS[params.problem]
    move = MOVES[params.move]

    a1 = world.add(Entity(id=params.animal1, kind="character", type=a1k.pronoun_type, label=a1k.label, role="helper"))
    a2 = world.add(Entity(id=params.animal2, kind="character", type=a2k.pronoun_type, label=a2k.label, role="helper"))
    team = world.add(Entity(id="teamwork", kind="thing", label="teamwork", role="idea"))
    tool = world.add(Entity(id="doohicky", kind="thing", label=doh.label, role="tool"))
    problem_ent = world.add(Entity(id="problem", kind="thing", label=prob.label, role="problem"))

    a1.memes["hope"] += 1
    a2.memes["hope"] += 1
    a1.meters["teamwork"] += 1
    a2.meters["teamwork"] += 1

    world.say(random.choice(GREETINGS))
    world.say(f"On the pier, {a1.id} and {a2.id} spotted a {doh.label} that was needed to {doh.purpose}.")
    world.say(scene["detail"])
    world.para()
    world.say(f"But the {prob.label} made trouble: {prob.mess}, and it {prob.blocks}.")
    world.say(f'"We can fix it," said {a1.id}, and {a2.id} nodded. "We should do it together."')
    world.para()
    world.say(f"{a1.id} and {a2.id} took hold of the {doh.label} and {move.text}.")
    if params.move in {"pull", "twist"}:
        world.say(f"The {doh.label} answered with a small creak, and then it moved.")
    else:
        world.say(f"The {doh.label} shifted in the right direction, slow at first, then easy.")
    a1.meters["teamwork"] += 1
    a2.meters["teamwork"] += 1
    a1.meters["success"] += 1
    a2.meters["success"] += 1
    a1.memes["pride"] += 1
    a2.memes["pride"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f"At last, {move.qa_text} and the {prob.label} was fixed.")
    world.say(f"The doohicky was no longer stuck; {a1.id} and {a2.id} stood beside it, smiling at the water.")
    world.say(f"Below them, the little waves kept tapping the pier, but now the team had the job done.")

    world.facts.update(
        setting=scene,
        animal1=a1,
        animal2=a2,
        doohicky=doh,
        problem=prob,
        move=move,
        tool=tool,
        problem_ent=problem_ent,
        outcome="fixed",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly animal story on a pier that includes the word '{f['doohicky'].label}'.",
        f"Tell a short teamwork story where {f['animal1'].id} and {f['animal2'].id} work together on the pier to fix a {f['problem'].label}.",
        f"Write an Animal Story style tale with a pier setting, a doohicky, and a happy ending that shows teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a1 = f["animal1"].id
    a2 = f["animal2"].id
    prob = f["problem"].label
    doh = f["doohicky"].label
    return [
        QAItem(question="Who worked together in the story?", answer=f"{a1} and {a2} worked together. They both held the doohicky and fixed the problem as a team."),
        QAItem(question="What was wrong on the pier?", answer=f"There was a {prob}. It blocked the job and made the pier scene tricky until the animals solved it together."),
        QAItem(question="How did the animals solve the problem?", answer=f"They used the {doh} and worked as a team. Their teamwork made the stuck thing move, and that changed the ending from stuck to fixed."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pier?", answer="A pier is a long wooden or stone walkway that sticks out over the water. People and animals can stand on it to look at the waves."),
        QAItem(question="What does teamwork mean?", answer="Teamwork means people or animals help each other do a job. Each one does a part, and together they can finish more easily."),
        QAItem(question="What is a doohicky?", answer="A doohicky is a made-up word for a small object or gadget. In a story, it usually means some handy thing with a special job."),
    ]


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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


def valid_combos_text() -> list[str]:
    return [f"{s},{a1},{a2},{d},{p},{m}" for s, a1, a2, d, p, m in valid_combos()]


ASP_RULES = r"""
valid(S,A1,A2,D,P,M) :- setting(S), animal(A1), animal(A2), A1 != A2, doohicky(D), problem(P), move(M),
                        compatible(P,M).
compatible(stuck_net,pull).
compatible(stuck_net,twist).
compatible(fallen_basket,steady).
compatible(heavy_crate,push).
compatible(heavy_crate,pull).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for d in DOOHICKIES:
        lines.append(asp.fact("doohicky", d))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for m in MOVES:
        lines.append(asp.fact("move", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, animal1=None, animal2=None, doohicky=None, problem=None, move=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_sample(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    return build_sample(params)


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
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.setting}: {p.animal1} + {p.animal2} with {p.doohicky} ({p.problem})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
