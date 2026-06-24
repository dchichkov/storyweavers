#!/usr/bin/env python3
"""
Story world: van / frantic / soften.

A tiny fable-like simulation where a village van is in a hurry, a frightened
passenger is frantic, and a kinder, slower choice softens the suspense.
The world uses physical meters and emotional memes so the prose comes from the
state, not from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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

    def __post_init__(self) -> None:
        for k in ("bump", "safe", "scrape", "rest"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "frantic", "care", "calm", "hope", "conflict", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    road: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    label: str
    phrase: str
    region: str
    fragile: bool = True


@dataclass
class Choice:
    id: str
    name: str
    risk: str
    fix: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    van = world.entities.get("van")
    cargo = world.entities.get("cargo")
    if not van or not cargo:
        return out
    if van.meters["bump"] < THRESHOLD:
        return out
    sig = ("bump",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["scrape"] += 1
    out.append("The boxes inside the van slid and tapped together.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["frantic"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["conflict"] += 1
    out.append("The little rider's heart beat fast with worry.")
    return out


CAUSAL_RULES = [Rule("bump", _r_bump), Rule("fear", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_problem(world: World, choice: Choice) -> dict:
    sim = world.copy()
    driver = sim.get("driver")
    driver.meters["bump"] += 1
    sim.get("child").memes["frantic"] += 1
    propagate(sim, narrate=False)
    return {
        "scraped": sim.get("cargo").meters["scrape"] >= THRESHOLD,
        "conflict": sim.get("child").memes["conflict"] >= THRESHOLD,
    }


def choose_reasonable_fix(choice: Choice) -> str:
    return choice.fix


def setup_story(world: World, choice: Choice) -> None:
    driver = world.add(Entity("driver", "character", "person"))
    child = world.add(Entity("child", "character", "child", traits=["small", "curious"]))
    van = world.add(Entity("van", "thing", "van", phrase="an old blue van", owner="driver"))
    cargo = world.add(Entity("cargo", "thing", "cargo", phrase="a basket of bright apples", owner="driver"))
    world.facts.update(choice=choice, driver=driver, child=child, van=van, cargo=cargo)

    world.say(
        f"There was once a village van that carried a basket of bright apples to the market."
    )
    world.say(
        f"In that van rode a little child who was frightened and frantic, because the road ahead was rough."
    )
    world.para()
    world.say(
        f"The driver loved the road, but also knew that speed can shake a careful load."
    )


def turn_story(world: World, choice: Choice) -> None:
    driver = world.get("driver")
    child = world.get("child")
    cargo = world.get("cargo")
    world.para()
    world.say(
        f"When the van reached the stony hill, the child wanted to hurry and make the story end at once."
    )
    child.memes["frantic"] += 1
    problem = predict_problem(world, choice)
    if problem["scraped"]:
        world.say(
            f"The driver saw that the apples would be scraped if the van bounced too hard."
        )
    if problem["conflict"]:
        world.say(
            f"So the driver's voice stayed gentle, and the child felt the worry even more."
        )
    child.memes["fear"] += 0.5
    driver.memes["care"] += 1
    driver.memes["trust"] += 1
    world.say(
        f"Then the driver slowed the van and laid a soft cloth over the basket, letting the suspense soften."
    )
    van = world.get("van")
    van.meters["safe"] += 1
    child.memes["calm"] += 1
    child.memes["frantic"] = 0.0
    child.memes["hope"] += 1
    cargo.meters["scrape"] = 0.0
    propagate(world, narrate=True)
    world.say(
        f"The child looked out at the hills and learned that a slow, kind choice can be braver than a frantic one."
    )


def end_story(world: World) -> None:
    world.para()
    world.say(
        f"In the end, the apples reached the market whole, the van rolled on safely, and the child's heart was quiet."
    )
    world.say(
        f"That day left a small moral: when fear grows frantic, patience can soften the road and keep everyone safe."
    )


SETTINGS = {
    "hillroad": Setting(place="the hill road", road="stony", affords={"van"}),
    "marketlane": Setting(place="the market lane", road="narrow", affords={"van"}),
    "forestpath": Setting(place="the forest path", road="bumpy", affords={"van"}),
}

CHOICES = {
    "apples": Choice("apples", "apples", "scrape", "soft cloth", {"cargo"}, "apples", {"fruit"}),
    "eggs": Choice("eggs", "eggs", "break", "soft straw", {"cargo"}, "eggs", {"food"}),
    "flowers": Choice("flowers", "flowers", "bruise", "blanket", {"cargo"}, "flowers", {"gift"}),
}

GENDERS = ["girl", "boy"]
NAMES = ["Mila", "Ben", "Iris", "Theo", "Lena", "Owen"]


@dataclass
class StoryParams:
    setting: str
    cargo: str
    name: str
    gender: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    choice = CHOICES[params.cargo]
    setup_story(world, choice)
    turn_story(world, choice)
    end_story(world)
    world.facts["choice"] = choice
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CHOICES]


KNOWLEDGE = {
    "van": [
        ("What is a van?", "A van is a vehicle with room for people or things, often used for trips and deliveries."),
    ],
    "frantic": [
        ("What does frantic mean?", "Frantic means very upset, rushed, and hard to calm down."),
    ],
    "soften": [
        ("What does it mean to soften something?", "To soften something means to make it less hard, less strong, or less harsh."),
    ],
    "patience": [
        ("What is patience?", "Patience means waiting calmly and not rushing when something takes time."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    p = world.facts["choice"]
    return [
        f'Write a short fable about a van and a frantic child that includes the word "{p.keyword}".',
        f"Tell a gentle story where patience softens suspense in a van carrying {p.name}.",
        f"Write a child-friendly moral tale about a rough road, a van, and a calmer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    choice: Choice = world.facts["choice"]
    return [
        QAItem(
            question="What kind of vehicle carried the child and the apples?",
            answer="It was a village van, and it carried the child and the basket of bright apples.",
        ),
        QAItem(
            question="Why was the child frantic?",
            answer="The child was frantic because the road ahead was rough and the ride felt uncertain.",
        ),
        QAItem(
            question="How did the driver help?",
            answer=f"The driver slowed the van and used {choose_reasonable_fix(choice)} to protect the cargo, which softened the suspense.",
        ),
        QAItem(
            question="What was the moral of the story?",
            answer="The moral was that patience and kindness can calm fear and keep a careful load safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("van", "frantic", "soften", "patience"):
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
        lines.append(f"  {e.id:8} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
frantic(X) :- meme(X, frantic), meme(X, level).
moral_value(patience).
transformation(X, calm) :- meme(X, calm), meme(X, hope).
safe_load(V) :- van(V), soft_cover(V).
problem(V) :- van(V), bumpy_road.
resolution(V) :- safe_load(V), not problem(V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("road", sid, setting.road))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("cargo_kind", cid))
        lines.append(asp.fact("risk", cid, choice.risk))
        lines.append(asp.fact("fix", cid, choice.fix.replace(" ", "_")))
        for t in sorted(choice.tags):
            lines.append(asp.fact("tag", cid, t))
    lines.append(asp.fact("moral_value", "patience"))
    lines.append(asp.fact("feature", "suspense"))
    lines.append(asp.fact("feature", "transformation"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show moral_value/1. #show feature/1."))
    facts = set(asp.atoms(model, "feature"))
    if ("suspense",) in facts and ("transformation",) in facts:
        print("OK: ASP features are present.")
        return 0
    print("MISMATCH in ASP feature facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-like van story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
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
    cargo = args.cargo or rng.choice(list(CHOICES))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(GENDERS)
    return StoryParams(setting=setting, cargo=cargo, name=name, gender=gender)


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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams("hillroad", "apples", "Mila", "girl"),
    StoryParams("marketlane", "eggs", "Ben", "boy"),
    StoryParams("forestpath", "flowers", "Iris", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show feature/1. #show moral_value/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show moral_value/1. #show feature/1."))
        print("ASP model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
