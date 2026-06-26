#!/usr/bin/env python3
"""
A folk-tale storyworld about a village system, a vacancy, and a test of
curiosity, with sharing as the gentle resolution.

The seed premise:
- A small village has a well-ordered system for tending the lantern path.
- A helper role becomes vacant when the old lantern-keeper grows tired.
- A curious child wants to take the test for the vacancy.
- The child first learns to share tools and attention, then passes the test and
  joins the village system.

The story is generated from stateful simulation, not a frozen paragraph:
- physical meters track carried items, light, and readiness
- emotional memes track curiosity, worry, pride, and trust
- the ending proves what changed in the village system
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village green"
    affords: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    verb: str
    gerund: str
    clue: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vacancy:
    id: str
    title: str
    tool: str
    tool_phrase: str
    shareable: str
    test_item: str
    reward: str
    threshold_kind: str = "readiness"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter(e, key) + amt


def add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme(e, key) + amt


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in [e for e in world.entities.values() if e.kind == "character"]:
            if meme(actor, "curiosity") >= THRESHOLD and meme(actor, "worry") >= THRESHOLD:
                sig = ("focus", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    add_meme(actor, "focus", 1.0)
                    out.append(f"{actor.id} grew quiet and looked closely at the work.")
                    changed = True

            if meter(actor, "sharing") >= THRESHOLD and meme(actor, "trust") < THRESHOLD:
                sig = ("trust", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    add_meme(actor, "trust", 1.0)
                    out.append(f"That made the others trust {actor.id} more.")
                    changed = True

            if meter(actor, "ready") >= THRESHOLD and meme(actor, "focus") >= THRESHOLD:
                sig = ("pass", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    add_meme(actor, "pride", 1.0)
                    out.append(f"{actor.id} was ready for the test at last.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTING = Setting(
    place="the village green",
    affords={"listening", "sharing", "test"},
)

TRIALS = {
    "lantern_test": Trial(
        id="lantern_test",
        verb="take the lantern test",
        gerund="taking the lantern test",
        clue="a bright wick and a careful hand",
        risk="the flame could go out",
        weather="foggy",
        keyword="test",
        tags={"test", "light"},
    )
}

VACANCIES = {
    "lantern_keeper": Vacancy(
        id="lantern_keeper",
        title="lantern keeper",
        tool="lantern",
        tool_phrase="the old brass lantern",
        shareable="oil and matches",
        test_item="wick",
        reward="the key to the lamp shed",
    )
}

GIRL_NAMES = ["Mira", "Nela", "Tova", "Lina", "Sera", "Rin"]
BOY_NAMES = ["Ivo", "Pavel", "Borin", "Marek", "Tarin", "Jori"]
ADJ = ["curious", "kind", "patient", "brave", "gentle", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("village", "lantern_test", "lantern_keeper")]


@dataclass
class StoryParams:
    place: str
    trial: str
    vacancy: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale world about sharing, curiosity, and a vacant village role."
    )
    ap.add_argument("--place", choices=["village"])
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--vacancy", choices=VACANCIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    trial = args.trial or "lantern_test"
    vacancy = args.vacancy or "lantern_keeper"
    if args.trial and args.trial not in TRIALS:
        raise StoryError("Unknown trial.")
    if args.vacancy and args.vacancy not in VACANCIES:
        raise StoryError("Unknown vacancy.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(ADJ)
    return StoryParams("village", trial, vacancy, name, gender, elder, trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.trial != "lantern_test" or params.vacancy != "lantern_keeper":
        raise StoryError("This tale only grows around the lantern test and the lantern-keeper vacancy.")


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder, label=params.elder))
    vacancy = VACANCIES[params.vacancy]
    trial = TRIALS[params.trial]
    lantern = world.add(Entity(
        id="Lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase=vacancy.tool_phrase,
        owner=elder.id,
        caretaker=elder.id,
    ))

    add_meme(hero, "curiosity", 1.0)
    world.say(
        f"In the village by the green, there was an old system for lighting the path each evening."
    )
    world.say(
        f"The lantern keeper watched over {vacancy.tool_phrase}, and the little folk knew where to stand, where to wait, and where to help."
    )
    world.say(
        f"{hero.id} was a {params.trait} {params.gender} who loved to ask why the bells rang and why the windows shone."
    )
    world.para()

    add_meme(hero, "desire", 1.0)
    world.say(
        f"One foggy dusk, the village announced a vacancy: the lantern keeper needed a helper who could learn the work."
    )
    world.say(
        f"{hero.id} wanted to take the {trial.keyword} test at once, but {params.elder} warned that the task was not solved by hurry."
    )
    add_meme(hero, "worry", 1.0)
    world.say(
        f'The elder said, "{trial.clue} matters most, because {trial.risk} when the mist is thick."'
    )

    world.para()
    add_meter(hero, "sharing", 1.0)
    add_meme(hero, "curiosity", 1.0)
    world.say(
        f"Before the test, {hero.id} shared the oil, the matches, and even a little stool with the younger children."
    )
    world.say(
        f"The children showed {hero.id} how to hold the lantern steady, and {hero.id} listened instead of boasting."
    )
    propagate(world)

    add_meter(hero, "ready", 1.0)
    world.say(
        f"Then {hero.id} stepped to the test with a calm heart and a careful hand."
    )
    world.say(
        f"{hero.id} cleaned the wick, shielded the flame from the fog, and kept the light bright from start to end."
    )
    add_meter(lantern, "light", 1.0)
    propagate(world)

    world.para()
    add_meme(hero, "pride", 1.0)
    add_meme(elder, "trust", 1.0)
    world.say(
        f"The elder smiled and gave {hero.id} the key to the lamp shed, because the village system had found its new keeper."
    )
    world.say(
        f"That night, {hero.id} carried {vacancy.tool_phrase} along the path, and the whole green glowed as if it had been waiting for {hero.id} all along."
    )

    world.facts.update(hero=hero, elder=elder, vacancy=vacancy, trial=trial, lantern=lantern)
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trial = f["trial"]
    vacancy = f["vacancy"]
    return [
        f'Write a short folk tale for young children about a village system, a vacancy, and a curiosity test that includes the word "{trial.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {trial.verb} for the {vacancy.title} vacancy, but learns to share first.",
        f"Write a simple village tale about {hero.id}, a lantern, and a child who proves readiness by sharing and careful attention.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    vacancy = f["vacancy"]
    trial = f["trial"]
    return [
        QAItem(
            question=f"Who wanted to take the {trial.keyword} test for the vacant village job?",
            answer=f"{hero.id}, a curious child in the village, wanted to take the test for the vacant {vacancy.title} job.",
        ),
        QAItem(
            question=f"Why did the elder worry about the test?",
            answer=f"The elder worried because {trial.risk}, so the test had to be done with a calm hand and careful attention.",
        ),
        QAItem(
            question=f"What did {hero.id} share before the test?",
            answer=f"{hero.id} shared the oil, the matches, and even a little stool with the younger children, which helped everyone trust {hero.id}.",
        ),
        QAItem(
            question=f"How did {hero.id} finally earn the vacancy?",
            answer=f"{hero.id} kept the flame steady during the test, and the elder gave {hero.id} the key to the lamp shed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vacancy?",
            answer="A vacancy is an open place or job that no one is filling yet, so someone new may be chosen for it.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing helps because it lets everyone use what they need, and it can make people trust one another more.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions and learn how things work.",
        ),
        QAItem(
            question="Why do lanterns help people at night?",
            answer="Lanterns give light in the dark, so people can see the path more clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(village, lantern_test, lantern_keeper).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "village"),
        asp.fact("trial", "lantern_test"),
        asp.fact("vacancy", "lantern_keeper"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combo).")
        return 0
    print("MISMATCH")
    return 1


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


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
    StoryParams("village", "lantern_test", "lantern_keeper", "Mira", "girl", "grandmother", "curious"),
    StoryParams("village", "lantern_test", "lantern_keeper", "Ivo", "boy", "grandfather", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.trial} / {p.vacancy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
