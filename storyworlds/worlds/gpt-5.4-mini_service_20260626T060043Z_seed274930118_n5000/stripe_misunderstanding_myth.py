#!/usr/bin/env python3
"""
storyworlds/worlds/stripe_misunderstanding_myth.py
==================================================

A small story world about a mythic stripe, a troubling misunderstanding, and a
gentle correction.

Seed premise:
- In a village of old stories, a stripe is taken for a warning.
- The villagers fear what they do not understand.
- A child and a keeper of tales discover the stripe is not a threat but a sign.
- The ending should feel mythic: the fear turns into a blessing, and the world
  is a little kinder for it.

This script follows the storyworld contract:
- self-contained stdlib script
- typed entities with meters and memes
- story-driven simulation
- inline ASP twin and Python reasonableness gate
- QA, trace, JSON, verify, and show-asp support
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
        if self.type in {"girl", "woman", "mother", "elder"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MythObject:
    id: str
    label: str
    phrase: str
    sign: str
    meaning: str
    color: str = "stripe"
    kind: str = "token"


@dataclass
class StoryParams:
    place: str
    sign: str
    name: str
    gender: str
    keeper: str
    mood: str
    seed: Optional[int] = None


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (rule_reveal, rule_calm, rule_blessing):
            sents = fn(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def rule_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"])
    sign = world.get(world.facts["sign"])
    elder = world.get(world.facts["elder"])
    if child.memes.get("fear", 0) >= THRESHOLD and world.facts.get("truth_told") and ("reveal", child.id) not in world.fired:
        world.fired.add(("reveal", child.id))
        child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
        child.memes["understanding"] = child.memes.get("understanding", 0) + 1
        sign.memes["misunderstood"] = max(0.0, sign.memes.get("misunderstood", 0) - 1)
        out.append(f"{elder.label.capitalize()} spoke the old meaning of the stripe, and the fear began to loosen.")
    return out


def rule_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"])
    if child.memes.get("understanding", 0) >= THRESHOLD and ("calm", child.id) not in world.fired:
        world.fired.add(("calm", child.id))
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        child.memes["dread"] = 0.0
        out.append("The child breathed easier, as if a heavy stone had been lifted from the chest.")
    return out


def rule_blessing(world: World) -> list[str]:
    out: list[str] = []
    sign = world.get(world.facts["sign"])
    river = world.get(world.facts["river"])
    if world.facts.get("truth_told") and ("blessing", sign.id) not in world.fired:
        world.fired.add(("blessing", sign.id))
        sign.meters["glow"] = sign.meters.get("glow", 0) + 1
        river.meters["safe"] = river.meters.get("safe", 0) + 1
        out.append("Then the stripe shone like moon-thread, and the river path looked safe to follow.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    return _propagate(world, narrate=narrate)


def problem_is_reasonable(place: str, sign: MythObject) -> bool:
    return place in SETTINGS and sign.sign == "stripe"


def select_sign(place: str, rng: random.Random) -> MythObject:
    sign = rng.choice(list(SIGNS.values()))
    if not problem_is_reasonable(place, sign):
        raise StoryError("That combination does not make a sensible mythic misunderstanding.")
    return sign


def predict_truth(world: World, child_id: str, sign_id: str) -> bool:
    sim = world.copy()
    child = sim.get(child_id)
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    sim.facts["truth_told"] = True
    propagate(sim, narrate=False)
    return sim.get(sign_id).meters.get("glow", 0) >= 1


def introduce(world: World, child: Entity, keeper: Entity, sign: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived a small {child.type} named {child.id} and a keeper of tales named {keeper.id}."
    )
    world.say(
        f"One evening they found {sign.phrase}, and the stripe upon it looked strange under the fading light."
    )


def misunderstanding(world: World, child: Entity, keeper: Entity, sign: Entity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    sign.meters["seen"] = sign.meters.get("seen", 0) + 1
    world.say(
        f"{child.id} thought the stripe meant trouble, and the little heart began to race."
    )
    world.say(
        f"Some in the village whispered that the stripe was an omen, but {keeper.id} only looked more closely."
    )


def old_story(world: World, keeper: Entity, sign: Entity) -> None:
    world.say(
        f'{keeper.id} said, "This stripe is not a wound. It is a road-mark left by the moon for travelers who lose their way."'
    )
    world.facts["truth_told"] = True
    sign.memes["misunderstood"] = max(0.0, sign.memes.get("misunderstood", 0) - 1)


def turn(world: World, child: Entity, keeper: Entity, sign: Entity) -> None:
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0) - 1)
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    world.say(
        f"{child.id} bent near the stripe and saw that it matched the silver reeds by the water."
    )
    world.say(
        f"Then {keeper.id} pointed to the river, where the same stripe appeared again, shining faintly in the dark."
    )


def resolution(world: World, child: Entity, keeper: Entity, sign: Entity, river: Entity) -> None:
    propagate(world, narrate=True)
    world.say(
        f"{child.id} smiled, because the thing that had seemed frightening was only a guide."
    )
    world.say(
        f"Together they followed the stripe to the riverbank, and the water carried them home without fear."
    )
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    keeper.memes["pride"] = keeper.memes.get("pride", 0) + 1
    river.meters["safe"] = river.meters.get("safe", 0) + 1


SETTINGS = {
    "riverbank": Setting(place="the riverbank", mood="silver", affords={"look"}),
    "hill": Setting(place="the hill above the village", mood="windy", affords={"look"}),
    "cave": Setting(place="the cave of echoes", mood="quiet", affords={"look"}),
}

SIGNS = {
    "moonstripe": MythObject(
        id="moonstripe",
        label="a moon-striped stone",
        phrase="a moon-striped stone",
        sign="stripe",
        meaning="a guide mark for travelers",
    ),
    "foxstripe": MythObject(
        id="foxstripe",
        label="a stripe-marked fox statue",
        phrase="a stripe-marked fox statue",
        sign="stripe",
        meaning="a shrine that guards lost paths",
    ),
    "riverstripe": MythObject(
        id="riverstripe",
        label="a stripe in the river water",
        phrase="a stripe in the river water",
        sign="stripe",
        meaning="a path of reflected moonlight",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Suri", "Ira", "Nia", "Tala"]
BOY_NAMES = ["Kai", "Oren", "Bram", "Niko", "Joss", "Rian"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for sign in SIGNS:
            combos.append((place, sign))
    return combos


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy"))
    keeper = world.add(Entity(id=params.keeper, kind="character", type="elder", label=params.keeper))
    sign = world.add(Entity(id=params.sign, type="thing", label=SIGNS[params.sign].label, phrase=SIGNS[params.sign].phrase))
    river = world.add(Entity(id="river", type="thing", label="river", phrase="the river", meters={"safe": 0.0}, memes={"calm": 1.0}))

    world.facts.update(child=child.id, elder=keeper.id, sign=sign.id, river=river.id)
    introduce(world, child, keeper, sign)
    world.para()
    misunderstanding(world, child, keeper, sign)
    turn(world, child, keeper, sign)
    world.para()
    old_story(world, keeper, sign)
    resolution(world, child, keeper, sign, river)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about {world.get(f["sign"]).phrase} and the word "stripe".',
        f"Tell a gentle story in an old myth style where {world.get(f['child']).id} first misunderstands a stripe, then learns its true meaning.",
        f"Write a simple mythic tale set at {world.setting.place} where a stripe turns from a worry into a guide.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.get(world.facts["child"])
    keeper = world.get(world.facts["elder"])
    sign = world.get(world.facts["sign"])
    river = world.get(world.facts["river"])
    return [
        QAItem(
            question=f"Who was the child in the myth?",
            answer=f"The child was {child.id}, a little {child.type} who first thought the stripe meant trouble.",
        ),
        QAItem(
            question=f"Why did {child.id} worry about the stripe?",
            answer=f"{child.id} worried because the stripe looked strange at first, so it was easy to misunderstand it as a bad sign.",
        ),
        QAItem(
            question=f"What did the keeper of tales explain about the stripe?",
            answer=f"{keeper.id} explained that the stripe was not danger at all; it was a guide mark left for travelers who needed help finding the way.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the stripe shone like moon-thread, the river path felt safe, and {child.id} felt wonder instead of fear.",
        ),
        QAItem(
            question=f"Where did the child go at the end?",
            answer=f"{child.id} followed the stripe to the riverbank, and the safe river helped bring them home.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stripe?",
            answer="A stripe is a long line of color or light that runs across something.",
        ),
        QAItem(
            question="Why can people misunderstand a strange sign?",
            answer="People can misunderstand a strange sign when they do not know what it means and guess too quickly.",
        ),
        QAItem(
            question="What does a keeper of tales do?",
            answer="A keeper of tales remembers old stories and helps other people understand them.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
sign_is_stripe(S) :- sign(S), stripe_sign(S).
misunderstood(S) :- sign_is_stripe(S), fear(C), child(C).
truth_told(C) :- elder(E), speaks(E), child(C).
calm(C) :- truth_told(C), understood(C).
blessing(S) :- truth_told(_), sign_is_stripe(S).
#show misunderstood/1.
#show calm/1.
#show blessing/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        if sign.sign == "stripe":
            lines.append(asp.fact("stripe_sign", sid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("elder", "elder"))
    lines.append(asp.fact("speaks", "elder"))
    lines.append(asp.fact("understood", "child"))
    lines.append(asp.fact("fear", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show misunderstood/1.\n#show calm/1.\n#show blessing/1."))
    shown = set()
    for name in ("misunderstood", "calm", "blessing"):
        shown.update(asp.atoms(model, name))
    expected = {("misunderstood", ("child",)), ("calm", ("child",)), ("blessing", ("moonstripe",)), ("blessing", ("foxstripe",)), ("blessing", ("riverstripe",))}
    if shown == expected:
        print("OK: ASP twin is consistent with the declared facts.")
        return 0
    print("MISMATCH in ASP twin.")
    print(" got:", sorted(shown))
    print(" exp:", sorted(expected))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show blessing/1."))
    return sorted(set(asp.atoms(model, "blessing")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story about a stripe and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--keeper")
    ap.add_argument("--mood", choices=["silver", "windy", "quiet"])
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
    sign = args.sign or rng.choice(list(SIGNS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    keeper = args.keeper or rng.choice(["Ari", "Mara", "Sage", "Ivo"])
    mood = args.mood or SETTINGS[place].mood
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if sign not in SIGNS:
        raise StoryError("Unknown sign.")
    return StoryParams(place=place, sign=sign, name=name, gender=gender, keeper=keeper, mood=mood)


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
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show blessing/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        print(f"{len(asp_valid_combos())} blessing atoms:")
        for atom in asp_valid_combos():
            print(f"  {atom}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="riverbank", sign="moonstripe", name="Mina", gender="girl", keeper="Ari", mood="silver"),
            StoryParams(place="hill", sign="foxstripe", name="Kai", gender="boy", keeper="Sage", mood="windy"),
            StoryParams(place="cave", sign="riverstripe", name="Tala", gender="girl", keeper="Mara", mood="quiet"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.sign} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
