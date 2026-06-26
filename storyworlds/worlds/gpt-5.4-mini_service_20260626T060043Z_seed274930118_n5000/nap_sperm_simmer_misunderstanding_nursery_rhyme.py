#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nap_sperm_simmer_misunderstanding_nursery_rhyme.py
================================================================================================

A small standalone story world in a nursery-rhyme style.

Premise:
- A sleepy little sperm whale named Sperm loves naps.
- In a cozy nursery kitchen, a pot of oat porridge needs to simmer.
- A misunderstanding makes the child think "simmer" means "nap."
- The adult gently corrects the mix-up, and the story ends with warm porridge,
  a fixed misunderstanding, and a satisfied nap.

The world is intentionally tiny and classical: one child, one caregiver,
one simmering pot, one misunderstanding, and one resolution.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "maiden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery kitchen"
    affords: set[str] = field(default_factory=lambda: {"simmer"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    cue: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str = "Sperm"
    caregiver: str = "grandma"
    setting: str = "nursery_kitchen"
    action: str = "simmer"
    seed: Optional[int] = None


SETTINGS = {
    "nursery_kitchen": Setting(place="the nursery kitchen", affords={"simmer"}),
}

ACTIONS = {
    "simmer": Action(
        id="simmer",
        verb="simmer",
        gerund="simmering",
        cue="a gentle bubbling sound",
        effect="kept warm and soft",
        tags={"simmer"},
    ),
}

NAMES = ["Sperm", "Bubbles", "Nell", "Mina", "Toby"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    pot = world.get("pot")
    if child.memes.get("misunderstood", 0.0) < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confusion"] = child.memes.get("confusion", 0.0) + 1
    pot.meters["heat"] = pot.meters.get("heat", 0.0) - 0.5
    out.append("The little one frowned, because the word had gone all crooked in the air.")
    return out


def _r_simmer(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("pot")
    if pot.meters.get("heat", 0.0) < THRESHOLD:
        return out
    sig = ("simmer",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.meters["simmering"] = 1.0
    pot.meters["warmth"] = pot.meters.get("warmth", 0.0) + 1
    out.append("The porridge kept its tiny bubbles and stayed warm.")
    return out


def _r_resolve(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("confusion", 0.0) < THRESHOLD:
        return out
    sig = ("resolve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["understanding"] = child.memes.get("understanding", 0.0) + 1
    child.memes["confusion"] = 0.0
    out.append("Then the grown-up explained that simmer means a soft little bubble, not a sleepy nap.")
    return out


RULES = [
    Rule("misunderstanding", _r_misunderstanding),
    Rule("simmer", _r_simmer),
    Rule("resolve", _r_resolve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, action: Action, child_name: str, caregiver: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type="whale",
        label=child_name,
        meters={"sleep": 1.0},
        memes={"love_nap": 1.0, "curiosity": 1.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=caregiver,
        label=f"the {caregiver}",
        memes={"patience": 1.0},
    ))
    pot = world.add(Entity(
        id="pot",
        kind="thing",
        type="pot",
        label="porridge pot",
        phrase="a little pot of oat porridge",
        caretaker=adult.id,
        meters={"heat": 1.0, "simmering": 0.0, "warmth": 0.0},
    ))

    world.say(
        f"In {setting.place}, little {child.label} the sperm whale was sleepy as a toy in a box."
    )
    world.say(
        f"{child.label} loved a nap, and {adult.label} loved a gentle kitchen tune."
    )
    world.para()
    world.say(
        f"{adult.label} said, 'Let the porridge {action.verb}.'"
    )
    world.say(
        f"{child.label} heard the word and made a mix-up in a blink, for {action.cue} sounded like bedtime."
    )
    child.memes["misunderstood"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"The {action.id} kept on softly, and the {adult.label} smiled."
    )
    world.say(
        f"At last {child.label} tucked in for a nap while the porridge stayed {action.effect}."
    )
    world.facts.update(child=child, adult=adult, pot=pot, action=action, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    action = f["action"]
    return [
        f"Write a nursery-rhyme story about {child.label}, a sleepy sperm whale, who mishears the word '{action.id}'.",
        f"Tell a gentle story where {adult.label} explains that to {action.verb} is not the same as to nap.",
        "Make the ending cozy, musical, and clear enough for a small child to understand.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    action = f["action"]
    return [
        QAItem(
            question=f"Who was sleepy in the nursery kitchen?",
            answer=f"Little {child.label} the sperm whale was sleepy and loved a nap.",
        ),
        QAItem(
            question=f"What word did {child.label} misunderstand?",
            answer=f"{child.label} misunderstood the word '{action.id}' and thought it sounded like bedtime.",
        ),
        QAItem(
            question=f"How did the grown-up fix the misunderstanding?",
            answer=f"The {adult.label} explained that to {action.verb} means to make a soft, gentle bubble, not to go to sleep.",
        ),
        QAItem(
            question=f"What was the porridge doing by the end?",
            answer=f"The porridge was still {action.effect}, because it had kept on {action.gerund}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does simmer mean when cooking?",
            answer="To simmer means to cook with small, gentle bubbles, usually with low heat.",
        ),
        QAItem(
            question="What is a nap?",
            answer="A nap is a short sleep taken during the day when someone feels tired.",
        ),
        QAItem(
            question="Why do people gently explain words to children?",
            answer="People gently explain words so children can understand them and not get confused.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding :- child(child), hears(child, simmer), nap_loving(child).
simmering(pot) :- pot(pot), heat(pot).
resolved :- misunderstanding, explained(simmer, nap).
#show misunderstanding/0.
#show simmering/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("child", "child"),
        asp.fact("pot", "pot"),
        asp.fact("hears", "child", "simmer"),
        asp.fact("nap_loving", "child"),
        asp.fact("heat", "pot"),
        asp.fact("explained", "simmer", "nap"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show misunderstanding/0.\n#show simmering/1.\n#show resolved/0."))
    shown = {sym.name for sym in model}
    expected = {"misunderstanding", "simmering", "resolved"}
    if shown == expected:
        print("OK: ASP twin produced the expected nursery-rhyme model.")
        return 0
    print(f"Mismatch: got {sorted(shown)} expected {sorted(expected)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about nap, sperm, and simmer.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--caregiver", choices=["grandma", "mother", "father", "aunt"], default="grandma")
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
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        name=name,
        caregiver=args.caregiver,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], params.name, params.caregiver)
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
        print(asp_program("#show misunderstanding/0.\n#show simmering/1.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show misunderstanding/0.\n#show simmering/1.\n#show resolved/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(name=n, caregiver=args.caregiver)) for n in NAMES[:3]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
