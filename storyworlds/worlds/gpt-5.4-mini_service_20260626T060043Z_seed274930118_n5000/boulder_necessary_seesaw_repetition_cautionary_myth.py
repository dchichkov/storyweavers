#!/usr/bin/env python3
"""
A small mythic storyworld about a village, a necessary seesaw, and a boulder
that must be handled with care.

The seed image: in an old myth, a stone seesaw keeps two sides of the world in
balance. A child or novice is told the boulder is necessary to hold it down,
but repetition and caution matter: if the boulder is rolled carelessly, it can
crack the path, scare the goats, or upset the balance.

This script turns that premise into a tiny simulation with physical meters and
emotional memes, plus an inline ASP twin for the reasonableness gate.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def p(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Ritual:
    id: str
    verb: str
    gerund: str
    caution: str
    consequence: str
    keyword: str


@dataclass
class Boulder:
    label: str
    phrase: str
    region: str = "ground"


@dataclass
class Seesaw:
    label: str
    phrase: str
    balance: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_shake(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    boulder = world.entities.get("boulder")
    seesaw = world.entities.get("seesaw")
    if not hero or not boulder or not seesaw:
        return out
    if hero.meters.get("force", 0.0) < THRESHOLD:
        return out
    if world.facts.get("boulder_on_seesaw"):
        sig = ("shake",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        seesaw.meters["tilt"] = seesaw.meters.get("tilt", 0.0) + 1
        hero.memes["alarm"] = hero.memes.get("alarm", 0.0) + 1
        out.append("The seesaw gave a warning creak.")
    return out


CAUSAL_RULES = [_r_shake]


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


def reasonability_gate(setting: Setting, ritual: Ritual, boulder: Boulder, seesaw: Seesaw) -> bool:
    return "seesaw" in ritual.id and "boulder" in ritual.keyword and "balance" in seesaw.balance and "stone" in boulder.phrase


def predict(world: World, ritual: Ritual) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["force"] = 1.0
    sim.facts["boulder_on_seesaw"] = True
    propagate(sim, narrate=False)
    return {
        "tilt": sim.get("seesaw").meters.get("tilt", 0.0),
        "alarm": sim.get("hero").memes.get("alarm", 0.0),
    }


def tell(setting: Setting, ritual: Ritual, hero_name: str, hero_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id="elder", kind="character", type="priestess", label="the elder"))
    boulder = world.add(Entity(id="boulder", type="stone", label="boulder", phrase="a necessary stone boulder"))
    seesaw = world.add(Entity(id="seesaw", type="artifact", label="seesaw", phrase="an ancient seesaw of cedar and rope"))

    world.facts.update(hero=hero, elder=elder, boulder=boulder, seesaw=seesaw, ritual=ritual, setting=setting)

    world.say(f"In the old days, {setting.place} kept a mythic {seesaw.label} in the clearing.")
    world.say(f"The elder said the {boulder.label} was necessary, for it held the {seesaw.label} steady when the wind came.")
    world.say(f"Again and again, {hero.label} watched the same lesson: first the stone, then the balance, then the quiet.")

    world.para()
    world.say(f"One evening, {hero.label} wanted to {ritual.verb}, because the sky was red and the hill seemed to listen.")
    world.say(f'But the elder warned, "{ritual.caution}"')

    world.para()
    hero.meters["force"] = 1.0
    hero.memes["worry"] = 0.0
    world.facts["boulder_on_seesaw"] = True
    pred = predict(world, ritual)
    if pred["tilt"] > 0:
        hero.memes["worry"] += 1
        world.say(f"{hero.label} remembered the warning and rolled the stone only once, slowly, with both hands.")
        world.say(f"The {seesaw.label} answered with a deep, careful stillness.")
        world.say(f"The boulder stayed where it was necessary, and the hill did not shake.")
    else:
        world.say(f"{hero.label} pressed on, and the myth held its breath.")
        world.say(f"Nothing broke, but everyone learned that some stones must be moved with caution, not hurry.")

    world.facts["pred"] = pred
    return world


SETTINGS = {
    "clearing": Setting(place="the sunlit clearing", affords={"ritual"}),
    "hill": Setting(place="the old hill", affords={"ritual"}),
    "shrine": Setting(place="the shrine road", affords={"ritual"}),
}

RITUALS = {
    "seesaw": Ritual(
        id="seesaw",
        verb="push the seesaw in the old way",
        gerund="pushing the seesaw in the old way",
        caution="Do not rush the stone, or the balance will complain.",
        consequence="the balance held fast",
        keyword="boulder seesaw balance",
    ),
}

BOULDERS = {
    "stone_boulder": Boulder(label="boulder", phrase="a necessary stone boulder"),
}

SEE_SAWS = {
    "ancient": Seesaw(label="seesaw", phrase="an ancient seesaw of cedar and rope", balance="stone balance"),
}

GIRL_NAMES = ["Mira", "Nala", "Ira", "Suri", "Lena", "Tavi"]
BOY_NAMES = ["Orin", "Eli", "Pavo", "Rian", "Mako", "Toren"]


@dataclass
class StoryParams:
    place: str
    ritual: str
    name: str
    gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic storyworld about a necessary boulder and a seesaw.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    ritual = args.ritual or "seesaw"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, ritual=ritual, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children about {f["hero"].label}, a necessary boulder, and a seesaw that must be treated with caution.',
        f"Tell a cautionary story where {f['hero'].label} learns that some balances only stay true if the stone is moved slowly.",
        f'Write a gentle myth that repeats the lesson: "slow hands, steady stone, safe balance."',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"Why was the boulder important in the story?",
            answer=f"The boulder was necessary because it helped keep the seesaw steady in the clearing.",
        ),
        QAItem(
            question=f"What did {hero.label} need to remember about the boulder?",
            answer=f"{hero.label} needed to remember the warning and move the boulder slowly, with caution, so the balance would not complain.",
        ),
        QAItem(
            question=f"What happened when {hero.label} handled the stone carefully?",
            answer=f"The seesaw stayed quiet and steady, and the boulder remained where it was necessary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boulder?",
            answer="A boulder is a very large rock.",
        ),
        QAItem(
            question="What is a seesaw?",
            answer="A seesaw is a long board that rocks up and down when weight changes from one side to the other.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before acting so something does not go wrong.",
        ),
        QAItem(
            question="What does repetition help people do?",
            answer="Repetition helps people remember a lesson or a pattern by hearing or doing it again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: ({e.type}) " + " ".join(bits))
    out.append(f"facts: {world.facts}")
    return "\n".join(out)


ASP_RULES = r"""
place(clearing). place(hill). place(shrine).
ritual(seesaw).
boulder(stone_boulder).
seesaw(ancient).

necessary(B) :- boulder(B), stone_boulder(B).
cautionary(R) :- ritual(R), R = seesaw.
mythic_story(P,R,B,S) :- place(P), ritual(R), boulder(B), seesaw(S), necessary(B), cautionary(R).
#show mythic_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for r in RITUALS:
        lines.append(asp.fact("ritual", r))
    for b in BOULDERS:
        lines.append(asp.fact("boulder", b))
    for s in SEE_SAWS:
        lines.append(asp.fact("seesaw", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mythic_story/4."))
    atoms = set(asp.atoms(model, "mythic_story"))
    expected = {("clearing", "seesaw", "stone_boulder", "ancient"),
                ("hill", "seesaw", "stone_boulder", "ancient"),
                ("shrine", "seesaw", "stone_boulder", "ancient")}
    if atoms != expected:
        print("MISMATCH between ASP and python gate")
        print("asp:", sorted(atoms))
        print("expected:", sorted(expected))
        return 1
    print("OK: ASP parity verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RITUALS[params.ritual], params.name, params.gender)
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
        print(asp_program("#show mythic_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, ritual="seesaw", name="Mira", gender="girl")
            samples.append(generate(params))
    else:
        seen = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
