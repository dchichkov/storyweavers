#!/usr/bin/env python3
"""
storyworlds/worlds/jest_railroad_crossing_dialogue_folk_tale.py
===============================================================

A small folk-tale storyworld about a child, a jest, a railroad crossing, and
a careful turn from teasing to waiting.

Seed tale imagined from the prompt:
---
A little child loves to jest while walking by the railroad crossing.
An elder warns that a train is not a toy and that the bell must be heeded.
The child tries to hurry, but a crossing keeper lowers the gate and speaks
kindly. The child waits, the train passes, and the road opens safely.
---

World model:
---
- The crossing has a gate, a bell, a whistle, and a waiting post.
- The train advances toward the crossing with physical distance in meters.
- A hero's impatience and delight rise when they keep jesting.
- A keeper or elder can lower the gate, ring the bell, and calm the child.
- The ending should prove the change: the train has passed, the gate rises,
  and the child crosses safely with a lighter heart.
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

CROSSING_KIND = "railroad crossing"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "vehicle"
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
        male = {"boy", "father", "dad", "man", "uncle", "grandfather"}
        female = {"girl", "mother", "mom", "woman", "aunt", "grandmother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def title(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = CROSSING_KIND


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    risk: str
    fragility: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    prize: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mira", "Lina", "Tessa", "Nora", "Pia", "Wren"],
    "boy": ["Tobin", "Jasper", "Milo", "Robin", "Eli", "Galen"],
}
TRAITS = ["cheerful", "curious", "spry", "bold", "playful", "lively", "quick"]
PRIZES = {
    "basket": Prize(
        label="basket",
        phrase="a little basket of warm buns",
        type="basket",
        risk="would tip",
        fragility="the buns would scatter",
    ),
    "eggs": Prize(
        label="egg basket",
        phrase="a basket of fresh eggs",
        type="basket",
        risk="would rattle",
        fragility="the eggs might crack",
    ),
    "milk": Prize(
        label="milk pail",
        phrase="a small pail of milk",
        type="pail",
        risk="would splash",
        fragility="the milk might spill",
    ),
    "jam": Prize(
        label="jam jar",
        phrase="a glass jar of berry jam",
        type="jar",
        risk="would wobble",
        fragility="the jar might chip",
    ),
}
CURATED = [
    StoryParams(name="Mira", gender="girl", parent="grandmother", trait="cheerful", prize="basket"),
    StoryParams(name="Tobin", gender="boy", parent="uncle", trait="curious", prize="eggs"),
    StoryParams(name="Lina", gender="girl", parent="father", trait="playful", prize="milk"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for prize_id in PRIZES:
        combos.append((CROSSING_KIND, "wait", prize_id))
    return combos


def explain_rejection(prize_id: str) -> str:
    return f"(No story: the {PRIZES[prize_id].label} is not set up for this crossing tale.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} doesn't fit that gender choice here; try {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a jest at a railroad crossing.")
    ap.add_argument("--place", choices=[CROSSING_KIND], default=CROSSING_KIND)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.prize and args.gender and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    if args.prize and args.prize not in PRIZES:
        raise StoryError(explain_rejection(args.prize))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["grandmother", "grandfather", "aunt", "uncle", "father", "mother"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait, prize=prize)


def _is_safe(world: World) -> bool:
    return world.get("gate").meters.get("closed", 0) >= THRESHOLD and world.get("train").meters.get("distance", 0) > 0


def predict_outcome(world: World, hero: Entity, prize: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["impulse"] += 1
    sim.get("train").meters["distance"] = 0.0
    return {
        "safe": _is_safe(sim),
        "spill": prize.meters.get("spill", 0) >= THRESHOLD,
    }


def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    elder = world.add(Entity(id="elder", kind="character", type=params.parent, label=f"the {params.parent}"))
    guard = world.add(Entity(id="guard", kind="character", type="man", label="the crossing keeper"))
    train = world.add(Entity(id="train", kind="vehicle", type="train", label="the train"))
    gate = world.add(Entity(id="gate", kind="thing", type="gate", label="the gate"))
    bell = world.add(Entity(id="bell", kind="thing", type="bell", label="the bell"))
    prize_cfg = PRIZES[params.prize]
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
    ))
    hero.meters["joy"] = 0.0
    hero.meters["impulse"] = 0.0
    hero.memes["jest"] = 0.0
    elder.memes["worry"] = 0.0
    train.meters["distance"] = 4.0
    gate.meters["closed"] = 0.0
    bell.meters["rang"] = 0.0
    prize.meters["spill"] = 0.0
    return world


def intro(world: World, hero: Entity, elder: Entity, prize: Entity, trait: str) -> None:
    world.say(
        f"Once in a little village, {hero.id} was a {trait} child who loved a jest, "
        f"and {hero.pronoun('possessive')} {elder.title} carried {prize.phrase} toward the {CROSSING_KIND}."
    )
    world.say(
        f"{hero.id} liked to speak in bright little riddles, as if every stone on the road might answer back."
    )


def approach(world: World, hero: Entity, elder: Entity, train: Entity) -> None:
    world.para()
    train.meters["distance"] = 2.0
    world.say(
        f"By the {CROSSING_KIND}, a whistle came thin and far."
    )
    world.say(
        f'"Hear that?" said {hero.id}. "It sounds like an iron goose with a cold in its throat."'
    )
    elder = world.get("elder")
    elder.memes["worry"] += 1
    world.say(
        f'"A train is no goose and no toy," said {elder.title}. "We stand still until the bell says go."'
    )


def challenge(world: World, hero: Entity, prize: Entity, train: Entity) -> None:
    hero.memes["jest"] += 1
    hero.memes["impulse"] += 1
    world.say(
        f'{hero.id} laughed and made a jest: "I could hop the rails quicker than a rabbit!"'
    )
    world.say(
        f"But the {prize.label} gave a small wobble in {hero.pronoun('possessive')} hands, and the whistle sounded closer."
    )
    if train.meters.get("distance", 0) <= 2.0:
        prize.meters["spill"] += 1


def ring_and_hold(world: World, guard: Entity, gate: Entity, bell: Entity, train: Entity) -> None:
    bell.meters["rang"] += 1
    gate.meters["closed"] += 1
    train.meters["distance"] = 1.0
    world.say(
        f'Then the crossing keeper rang the bell and lowered the gate. "Hold, friends," said {guard.title}. "Let the long iron snake pass first."'
    )
    world.say(
        f'The {CROSSING_KIND} grew quiet except for the clank of wheels in the distance.'
    )


def resolve(world: World, hero: Entity, elder: Entity, guard: Entity, gate: Entity, train: Entity, prize: Entity) -> None:
    world.para()
    hero.meters["joy"] += 1
    hero.memes["jest"] += 1
    world.say(
        f'{hero.id} stopped at once and said, "A jest is fine for pies and porridge, not for tracks."'
    )
    world.say(
        f'"That is the truth," said {elder.title}, smiling now. {guard.title} lifted the gate when the {train.label} had passed, and the road opened again.'
    )
    gate.meters["closed"] = 0.0
    train.meters["distance"] = 0.0
    world.say(
        f"Together they crossed safely, and {prize.phrase} stayed sound in {hero.pronoun('possessive')} arms while the village wind sang over the rails."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get(params.name)
    elder = world.get("elder")
    guard = world.get("guard")
    train = world.get("train")
    gate = world.get("gate")
    bell = world.get("bell")
    prize = world.get("prize")
    intro(world, hero, elder, prize, params.trait)
    approach(world, hero, elder, prize, train)
    challenge(world, hero, prize, train)
    ring_and_hold(world, guard, gate, bell, train)
    resolve(world, hero, elder, guard, gate, train, prize)
    world.facts.update(
        hero=hero,
        elder=elder,
        guard=guard,
        train=train,
        gate=gate,
        bell=bell,
        prize=prize,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        f'Write a short folk tale set at a "{CROSSING_KIND}" where {hero.id} makes a jest but learns to wait.',
        f"Tell a dialogue-rich story about {hero.id} carrying {prize.phrase} across the tracks with an elder and a crossing keeper.",
        f'Write a child-friendly tale that uses the word "jest" and ends with the gate opening after the train passes.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    guard = f["guard"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Who made the jest at the railroad crossing?",
            answer=f"{hero.id} made the jest, and the jest almost made {hero.pronoun('possessive')} hands rush too fast.",
        ),
        QAItem(
            question=f"Why did {elder.title} tell {hero.id} to wait?",
            answer=f"{elder.title} warned that the train was coming and that the {prize.label} needed steady hands.",
        ),
        QAItem(
            question=f"What did the crossing keeper do to keep everyone safe?",
            answer=f"{guard.title} rang the bell, lowered the gate, and let the train pass before anyone crossed.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the train had passed, the gate opened, and {hero.id} crossed safely with {prize.phrase}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    prize = f["prize"]
    return [
        QAItem(
            question="What is a railroad crossing?",
            answer="A railroad crossing is a place where a road meets train tracks, so people must look and wait for trains.",
        ),
        QAItem(
            question="Why does a crossing have a gate or bell?",
            answer="A gate and a bell help warn people that a train is near, so they can stop and stay safe.",
        ),
        QAItem(
            question="Why should you not joke about a train coming close?",
            answer="A train is very heavy and moves fast, so safety matters more than jokes when it is near the tracks.",
        ),
        QAItem(
            question=f"What can happen to a {prize.label} if it is rushed across the tracks?",
            answer=f"It can wobble, spill, or crack, which is why steady hands and waiting are the wiser choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A prize is at risk when the child tries to rush at the crossing while a train is near.
at_risk(P) :- prize(P), moving_train, rush.

% Safety requires the gate to be closed and the bell to have rung.
safe :- gate_closed, bell_rang, not moving_train.

valid_story(Gender, Prize) :- wears(Gender, Prize), prize(Prize), safe.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("crossing", "railroad_crossing"),
        asp.fact("moving_train") if True else "",
        asp.fact("rush"),
    ]
    lines = [x for x in lines if x]
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if "girl" in p.genders:
            lines.append(asp.fact("wears", "girl", pid))
        if "boy" in p.genders:
            lines.append(asp.fact("wears", "boy", pid))
    lines.append(asp.fact("gate_closed"))
    lines.append(asp.fact("bell_rang"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    combos = {(params.gender, params.prize) for params in CURATED}
    asp_set = set(asp_valid_stories())
    py_set = set((p.gender, p.prize) for p in CURATED)
    if asp_set == py_set:
        print(f"OK: clingo gate matches curated story combos ({len(asp_set)}).")
        return 0
    print("MISMATCH between clingo and python story sets.")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible story combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.prize} at the crossing"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
