#!/usr/bin/env python3
"""
apricot_conflict_adventure.py
=============================

A tiny storyworld about an apricot adventure with a clear conflict, a risky
choice, and a safer turn toward a better path.

Premise:
- A child loves exploring the orchard and wants to reach the ripe apricots.
- A gate, a creek, or a bramble patch can make the trip feel brave and tricky.
- A helper notices the risk and suggests a careful way to continue the adventure.
- The story resolves when the child accepts help and reaches the apricots safely.

The world model tracks:
- physical meters: distance, strain, damage, and progress
- emotional memes: excitement, worry, conflict, trust, relief

The story text is generated from the simulated state, not from a fixed template
with swapped nouns.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    includes: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    obstacle: str
    risk: str
    action: str
    rush: str
    recover: str
    danger_meter: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    prep: str
    finish: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _r_progress(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    challenge: Challenge = world.facts["challenge"]
    if child.meter("travel") < THRESHOLD:
        return out
    if child.meter(challenge.danger_meter) >= THRESHOLD:
        sig = ("hurt", challenge.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["scraped"] = child.meter("scraped") + 1
            child.memes["worry"] = child.meme("worry") + 1
            out.append(f"The rough way left {child.id} scratched.")
    return out


def propagate(world: World) -> None:
    while True:
        before = len(world.fired)
        _r_progress(world)
        if len(world.fired) == before:
            break


SETTING_REGISTRY = {
    "orchard": Setting(place="the apricot orchard", includes={"apricot", "tree", "gate", "creek"}),
    "hillside": Setting(place="the sunny hillside orchard", includes={"apricot", "path", "bramble"}),
}

CHALLENGES = {
    "creek": Challenge(
        id="creek",
        obstacle="a narrow creek",
        risk="the current could soak the basket and make the stones slippery",
        action="cross the creek",
        rush="dash over the stones",
        recover="step carefully across the plank",
        danger_meter="soaked",
        zone="feet",
        tags={"water", "adventure", "apricot"},
    ),
    "bramble": Challenge(
        id="bramble",
        obstacle="a prickly bramble patch",
        risk="the thorns could snag clothes and scratch hands",
        action="push through the brambles",
        rush="push straight through",
        recover="take the side path",
        danger_meter="scratched",
        zone="hands",
        tags={"thorn", "adventure", "apricot"},
    ),
}

AIDS = {
    "plank": Aid(
        id="plank",
        label="a wooden plank",
        phrase="a narrow wooden plank",
        helps={"creek"},
        covers={"feet"},
        prep="put the basket on one arm and use the plank",
        finish="crossed the creek on the plank",
    ),
    "gloves": Aid(
        id="gloves",
        label="soft gloves",
        phrase="a pair of soft gloves",
        helps={"bramble"},
        covers={"hands"},
        prep="pull on the gloves",
        finish="walked through the brambles without getting scratched",
    ),
}

NAMES = {
    "girl": ["Maya", "Lina", "Tessa", "Iris", "Nora"],
    "boy": ["Theo", "Finn", "Owen", "Eli", "Max"],
}


@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small apricot adventure world with conflict and a safe turn.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "sibling"])
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


def prize_for(challenge: Challenge) -> str:
    return "apricots"


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p, s in SETTING_REGISTRY.items() for c in s.includes if c in CHALLENGES]


def explain_rejection(place: str, challenge: str) -> str:
    return f"(No story: {place} does not support the {challenge} adventure.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.challenge:
        if (args.place, args.challenge) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.challenge))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(["mother", "father", "sibling"])
    return StoryParams(place=place, challenge=challenge, name=name, gender=gender, helper=helper)


def _do_travel(world: World, child: Entity, challenge: Challenge, narrate: bool = True) -> None:
    child.meters["travel"] = child.meter("travel") + 1
    child.memes["excitement"] = child.meme("excitement") + 1
    if challenge.id == "creek":
        child.meters["soaked"] = child.meter("soaked") + 1
    else:
        child.meters["scratched"] = child.meter("scratched") + 1
    propagate(world)
    if narrate:
        world.say(f"{child.id} moved forward with brave steps.")


def predict_risk(world: World, child: Entity, challenge: Challenge, aid: Optional[Aid]) -> bool:
    sim = world.copy()
    c = sim.get(child.id)
    if aid:
        c.meters["travel"] = c.meter("travel") + 1
        if challenge.id == "creek" and "feet" not in aid.covers:
            c.meters["soaked"] = c.meter("soaked") + 1
        if challenge.id == "bramble" and "hands" not in aid.covers:
            c.meters["scratched"] = c.meter("scratched") + 1
    else:
        _do_travel(sim, c, challenge, narrate=False)
    return c.meter("soaked") >= THRESHOLD or c.meter("scratched") >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    challenge = CHALLENGES[params.challenge]
    aid = AIDS["plank" if challenge.id == "creek" else "gloves"]
    world.facts.update(child=child, helper=helper, challenge=challenge, aid=aid)

    world.say(f"{child.id} loved exploring {world.setting.place} for ripe apricots.")
    world.say(f"Every branch looked like part of an adventure, and {child.pronoun('subject')} wanted the sweetest fruit.")

    world.para()
    world.say(f"One day, {child.id} reached {challenge.obstacle}.")
    world.say(f"It looked exciting, but {challenge.risk}.")
    child.memes["desire"] = child.meme("desire") + 1
    child.memes["conflict"] = child.meme("conflict") + 1
    world.say(f"{child.id} wanted to {challenge.action}, yet {child.pronoun('possessive')} {params.helper} frowned at the danger.")
    world.say(f'"Let’s be careful," said {params.helper}. "We can still have an adventure."')

    world.para()
    if challenge.id == "creek":
        world.say(f"{child.id} tried to {challenge.rush}, but the stones were slick.")
    else:
        world.say(f"{child.id} tried to {challenge.rush}, but the thorns tugged close.")

    aid_ok = predict_risk(world, child, challenge, aid)
    if aid_ok:
        child.memes["trust"] = child.meme("trust") + 1
        world.say(f"{params.helper} showed {child.id} {aid.phrase} and said, \"{aid.prep}.\"")
        world.say(f"{child.id} nodded, let the hurry soften, and chose the safer path.")

    world.para()
    if challenge.id == "creek":
        child.meters["travel"] = child.meter("travel") + 1
        child.meters["soaked"] = 0
        child.memes["conflict"] = 0
        child.memes["relief"] = child.meme("relief") + 1
        world.say(f"Together they {aid.finish}, and the basket stayed dry.")
    else:
        child.meters["travel"] = child.meter("travel") + 1
        child.meters["scratched"] = 0
        child.memes["conflict"] = 0
        child.memes["relief"] = child.meme("relief") + 1
        world.say(f"Together they {aid.finish}, and the apricot path stayed gentle.")

    world.say(f"At last, {child.id} reached the tree and picked a warm apricot.")
    world.say(f"The fruit glowed like a tiny sunset in {child.pronoun('possessive')} hands.")
    world.facts["resolved"] = True
    return world


ASP_RULES = r"""
valid(place,challenge) :- setting(place), challenge(challenge), supports(place, challenge).
resolved(challenge) :- valid(_, challenge), has_aid(challenge).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", p))
        for c in sorted(s.includes):
            lines.append(asp.fact("supports", p, c))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for a in AIDS.values():
        lines.append(asp.fact("aid", a.id))
        for c in sorted(a.helps):
            lines.append(asp.fact("helps", a.id, c))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    challenge = f["challenge"]
    return [
        f'Write a short adventure story for a child named {child.id} and an apricot quest.',
        f"Tell a gentle conflict story where {child.id} wants to {challenge.action} but a helper worries.",
        f'Write a simple orchard adventure that includes "apricot" and ends safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    challenge: Challenge = f["challenge"]
    aid: Aid = f["aid"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at {world.setting.place}?",
            answer=f"{child.id} wanted to {challenge.action} so the child could reach the apricots.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry about the adventure?",
            answer=f"{helper.label} worried because {challenge.risk}.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.label} solve the conflict?",
            answer=f"They used {aid.label} and chose the safer way, so the apricots could be reached without trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an apricot?",
            answer="An apricot is a small orange fruit with soft skin and sweet flesh.",
        ),
        QAItem(
            question="What does it mean to be careful on a narrow path?",
            answer="It means moving slowly and paying attention so you do not slip or get hurt.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", challenge="creek", name="Maya", gender="girl", helper="mother"),
    StoryParams(place="hillside", challenge="bramble", name="Theo", gender="boy", helper="father"),
]


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


def build_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = list(valid_combos())
    if args.place or args.challenge:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.challenge is None or c[1] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(["mother", "father", "sibling"])
    return StoryParams(place=place, challenge=challenge, name=name, gender=gender, helper=helper)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Apricot adventure with conflict and a careful turn.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "sibling"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = build_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
