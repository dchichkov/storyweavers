#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/gigolo_curiosity_bedtime_story.py
===============================================================================================================

A small bedtime-story world about Curiosity, a soft mystery, and a gentle
return home. The seed word "gigolo" appears as the name of the curious child.

Premise:
- A little child named Gigolo loves wondering about quiet nighttime things.
- Curiosity leads Gigolo toward a glowing, sealed teacup of fireflies.
- A gentle caregiver notices the risk, explains, and offers a safer way to look.
- The ending image proves that curiosity was kept, but the danger was not.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    hush: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Curiosity:
    id: str
    verb: str
    gerund: str
    question: str
    pull: str
    risk: str
    keyword: str = "curiosity"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()

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
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


def _r_risk(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        if hero.meters.get("reach", 0.0) < THRESHOLD:
            continue
        for prize in world.entities.values():
            if prize.kind != "thing" or prize.label != "firefly jar":
                continue
            if "glow" not in world.zone:
                continue
            sig = ("risk", hero.id, prize.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            prize.meters["danger"] = 1.0
            out.append("The glowing jar looked tempting, but it was not a toy.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("calm", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
        out.append("A gentle plan helped everyone breathe slower.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_risk, _r_calm):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", hush="soft and sleepy", afford={"peek"}),
    "porch": Setting(place="the porch", hush="cool and quiet", afford={"peek"}),
    "attic": Setting(place="the attic", hush="dusty and dim", afford={"peek"}),
}

CURIOSITIES = {
    "curiosity": Curiosity(
        id="curiosity",
        verb="peek at the glowing jar",
        gerund="peeking at the glowing jar",
        question="What is that soft light?",
        pull="the tiny lights were dancing like stars",
        risk="the jar might tip and spill the fireflies",
        tags={"light", "night"},
    )
}

PRIZES = {
    "jar": Prize(
        label="jar",
        phrase="a little glass jar full of fireflies",
        type="jar",
        region="hands",
    ),
    "lantern": Prize(
        label="lantern",
        phrase="a small lantern with a warm candle",
        type="lantern",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="soft mittens",
        covers={"hands"},
        guards={"glow"},
        prep="put on soft mittens first",
        tail="tiptoed back with soft mittens on",
    ),
    Gear(
        id="tray",
        label="a little tray",
        covers={"hands"},
        guards={"glow"},
        prep="carry it on a little tray instead",
        tail="moved the jar onto a little tray",
    ),
]

NAMES = ["Gigolo", "Milo", "Nina", "Luna", "Pip", "Tessa"]
TRAITS = ["curious", "gentle", "sleepy", "bright-eyed"]


@dataclass
class StoryParams:
    place: str
    curiosity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for cur in CURIOSITIES:
            for prize in PRIZES:
                if prize == "jar":
                    combos.append((place, cur, prize))
    return combos


def explain_rejection(cur: Curiosity, prize: Prize) -> str:
    return f"(No story: this bedtime world only works when the curious glow and the firefly jar belong together.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about Curiosity and a glowing jar.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", dest="curiosity", choices=CURIOSITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.curiosity and args.prize and args.prize != "jar":
        raise StoryError(explain_rejection(CURIOSITIES[args.curiosity], PRIZES[args.prize]))
    place = args.place or rng.choice(list(SETTINGS))
    curiosity = args.curiosity or "curiosity"
    prize = args.prize or "jar"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place, curiosity, prize, name, gender, parent, trait)


def predict_risk(world: World, hero: Entity, curiosity: Curiosity, prize_id: str) -> bool:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    hero2.memes["curiosity"] = 1.0
    hero2.meters["reach"] = 1.0
    sim.zone = {"glow"}
    propagate(sim, narrate=False)
    return sim.get(prize_id).meters.get("danger", 0.0) >= THRESHOLD


def tell(setting: Setting, curiosity: Curiosity, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={"reach": 1.0}, memes={"curiosity": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="jar", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id))
    gear = world.add(Entity(id="gloves", type="gear", label="soft mittens", protective=True))
    world.facts.update(hero=hero, parent=parent, prize=prize, curiosity=curiosity, gear=gear, trait=trait)
    world.say(f"At {setting.place}, little {trait} {name} was a child with a very curious heart.")
    world.say(f"{name} loved bedtime best, because the room was {setting.hush} and the shadows were friendly.")
    world.say(f"One night, {name} heard {curiosity.question.lower()} and followed the soft glow near the shelf.")
    world.para()
    world.say(f"{name} wanted to {curiosity.verb}, but {name}'s {parent_type} smiled and held up a gentle hand.")
    world.say(f'"{curiosity.risk.capitalize()}," said the {parent_type}, "so let us be careful first."')
    if predict_risk(world, hero, curiosity, prize.id):
        hero.memes["worry"] = 1.0
        propagate(world)
        world.say(f"{name} pouted for a moment, because {curiosity.pull}.")
        world.para()
        world.say(f"Then the {parent_type} offered a safer idea: {GEAR[0].prep}.")
        world.say(f"{name} put on the mittens, and the little glow stayed bright and safe.")
        world.say(f"Together they {GEAR[0].tail}, and the fireflies blinked like tiny sleepy stars.")
    else:
        world.say(f"The glow stayed far away, and {name} simply waved and yawned.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cur = f["curiosity"]
    prize = f["prize"]
    return [
        f'Write a bedtime story for a young child about {hero.id} and {cur.keyword}, with a gentle glow and a safe choice.',
        f"Tell a soft story where {hero.id} wants to {cur.verb} but an adult helps keep {prize.label} safe.",
        f'Create a bedtime tale that includes the word "gigolo" as the child\'s name and ends with a calm, cozy image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    cur = f["curiosity"]
    return [
        QAItem(question=f"Who was the curious child in the story?", answer=f"The curious child was {hero.id}, and {hero.pronoun('subject')} loved quiet bedtime mysteries."),
        QAItem(question=f"What did {hero.id} want to do when the glow appeared?", answer=f"{hero.id} wanted to {cur.verb}, but the grown-up wanted to keep the jar safe."),
        QAItem(question=f"How did the {parent.type} help?", answer=f"The {parent.type} offered a safer plan and soft mittens so the fireflies could stay safe."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the feeling that makes you want to ask questions and learn about new things."),
        QAItem(question="Why should children be careful with glass jars?", answer="Glass jars can break if they are dropped, so it is safer for children to look with a grown-up's help."),
        QAItem(question="Why do fireflies glow?", answer="Fireflies glow because they make a tiny light in their bodies to find each other in the dark."),
    ]


ASP_RULES = r"""
curious(H) :- hero(H), curiosity(H).
risky(P) :- prize(P), glow_zone(P).
safe_fix(G,H,P) :- gear(G), protects(G,hands), curious(H), risky(P).
valid_story(P, H) :- safe_fix(_, H, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for c in CURIOSITIES:
        lines.append(asp.fact("curiosity_kind", c))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
        if p == "jar":
            lines.append(asp.fact("glow_zone", p))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in g.covers:
            lines.append(asp.fact("protects", g.id, c))
    lines.append(asp.fact("hero", "gigolo"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("jar", "gigolo")}
    if asp_set == py_set:
        print("OK: ASP and Python gates match.")
        return 0
    print("MISMATCH:", sorted(asp_set), sorted(py_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for item in sample.story_qa:
            print("Q:", item.question)
            print("A:", item.answer)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CURIOSITIES[params.curiosity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [StoryParams(place="nursery", curiosity="curiosity", prize="jar", name="Gigolo", gender="boy", parent="mother", trait="curious")]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        for i in range(max(1, args.n)):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            p.seed = args.seed
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
