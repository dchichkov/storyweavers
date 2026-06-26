#!/usr/bin/env python3
"""
A standalone storyworld for a small petting-zoo adventure mystery.

Premise:
A child visits a petting zoo where a sweet nectar treat has gone missing or
spoiled. A curious, cautious friend duo must solve the mystery without
aggravating the animals, while learning that gentle choices keep everyone safe.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    item_of: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the petting zoo"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Hunch:
    id: str
    label: str
    clue: str
    fix: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _scare(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for animal in world.entities.values():
            if animal.kind != "animal":
                continue
            if animal.id == actor.id:
                continue
            if animal.meters["calm"] < THRESHOLD:
                sig = ("aggravate", actor.id, animal.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                animal.memes["aggravated"] += 1
                out.append(f"The {animal.label} looked upset.")
    return out


def _spill_nectar(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["clumsy"] < THRESHOLD:
            continue
        if "nectar" not in world.entities:
            continue
        nectar = world.get("nectar")
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        nectar.meters["lost"] += 1
        out.append("The nectar was no longer where it had been.")
    return out


CAUSAL_RULES = [
    ("scare", _scare),
    ("spill_nectar", _spill_nectar),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_line(world: World) -> str:
    return f"The petting zoo was full of warm straw, small hooves, and curious eyes."


def introduce(world: World, child: Entity, friend: Entity, animal: Entity) -> None:
    world.say(
        f"{child.id} and {friend.id} arrived at {world.setting.place} for a tiny adventure."
    )
    world.say(
        f"They loved the {animal.label}, especially when it came close enough to sniff their hands."
    )


def mystery(world: World, child: Entity, friend: Entity, nectar: Entity) -> None:
    child.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"Then they spotted a little mystery: the sweet nectar cup was empty, "
        f"and a sticky trail led past the fence."
    )
    world.say(
        f"{child.id} wanted to investigate right away, but {friend.id} reminded {child.id} to stay cautious."
    )


def clue(world: World, animal: Entity, nectar: Entity) -> None:
    if nectar.meters["lost"] >= THRESHOLD:
        animal.memes["concern"] += 1
        world.say(
            f"The trail led to a crate near the goats, where one goat had shiny lips and a green leaf stuck to its beard."
        )


def aggravate_choice(world: World, child: Entity) -> None:
    child.meters["noise"] += 1
    world.say(
        f"{child.id} almost rushed forward and called out too loudly, which made the animals shift and twitch."
    )
    propagate(world, narrate=False)
    if any(e.memes["aggravated"] >= THRESHOLD for e in world.entities.values() if e.kind == "animal"):
        world.say("That was a bad idea, because the animals did not like being startled.")


def caution(world: World, friend: Entity) -> None:
    friend.memes["warning"] += 1
    world.say(
        f"{friend.id} held up a hand and whispered, 'Slow steps. Soft voices. We can solve this without bothering them.'"
    )


def solve(world: World, child: Entity, friend: Entity, animal: Entity, nectar: Entity) -> None:
    child.memes["brave"] += 1
    friend.memes["brave"] += 1
    animal.meters["calm"] += 1
    world.say(
        f"Together they followed the trail, noticed the nectar under a tipped scoop, and quietly set it back where it belonged."
    )
    world.say(
        f"The goat stopped worrying, and the little mystery was solved without any rough grabbing or shouting."
    )


def ending(world: World, child: Entity, friend: Entity, animal: Entity, nectar: Entity) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the end, {child.id} and {friend.id} petted the {animal.label} gently while the clean nectar cup sat safe on the bench."
    )
    world.say(
        f"It felt like a small adventure, and the best part was that everyone stayed calm and friendly."
    )


def tell() -> World:
    setting = Setting(place="the petting zoo", affords={"solve_mystery", "caution", "friendship"})
    world = World(setting)

    child = world.add(Entity(id="Mira", kind="character", type="girl", traits=["curious", "kind"]))
    friend = world.add(Entity(id="Jonah", kind="character", type="boy", traits=["cautious", "loyal"]))
    goat = world.add(Entity(id="goat", kind="animal", type="goat", label="goat", traits=["nervous"]))
    nectar = world.add(Entity(id="nectar", type="thing", label="nectar cup", phrase="a sticky nectar cup"))

    world.say(setting_line(world))
    introduce(world, child, friend, goat)

    world.para()
    mystery(world, child, friend, nectar)
    clue(world, goat, nectar)

    world.para()
    aggravate_choice(world, child)
    caution(world, friend)

    world.para()
    solve(world, child, friend, goat, nectar)
    ending(world, child, friend, goat, nectar)

    world.facts.update(
        child=child,
        friend=friend,
        animal=goat,
        nectar=nectar,
        setting=setting,
        mystery_solved=True,
        caution_used=True,
    )
    return world


SETTINGS = {
    "petting_zoo": Setting(place="the petting zoo", affords={"solve_mystery", "caution", "friendship"}),
}

ACTIVITIES = {
    "mystery": Activity(
        id="mystery",
        verb="solve the mystery",
        gerund="solving the mystery",
        rush="rush toward the clues",
        mess="noise",
        zone={"ears"},
        weather="",
        keyword="mystery",
        tags={"mystery", "adventure"},
    ),
    "caution": Activity(
        id="caution",
        verb="move carefully",
        gerund="moving carefully",
        rush="dash ahead",
        mess="noise",
        zone={"ears"},
        weather="",
        keyword="caution",
        tags={"caution"},
    ),
}

PRIZES = {
    "nectar": Prize(
        label="nectar",
        phrase="sweet nectar",
        type="nectar",
        region="hands",
    ),
}

HUNCHES = {
    "friendship": Hunch(
        id="friendship",
        label="friendship",
        clue="a soft voice and a shared plan",
        fix="work together",
        guards={"noise"},
    ),
    "caution": Hunch(
        id="caution",
        label="caution",
        clue="slow steps and quiet hands",
        fix="take it slowly",
        guards={"noise"},
    ),
}

NAMES = ["Mira", "Jonah", "Iris", "Theo", "Nia", "Owen", "Luna", "Eli"]
TRAITS = ["curious", "brave", "gentle", "careful", "kind", "loyal"]


@dataclass
class StoryParams:
    place: str = "petting_zoo"
    activity: str = "mystery"
    prize: str = "nectar"
    name: Optional[str] = None
    friend: Optional[str] = None
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("petting_zoo", "mystery", "nectar")]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    return [
        'Write a short Adventure story set in a petting zoo where a child solves a mystery involving nectar.',
        f"Tell a friendship story where {child.id} and {friend.id} use caution to solve a small mystery without aggravating the animals.",
        'Write a child-friendly story that includes the words "mystery", "friendship", "caution", and "nectar".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    animal = f["animal"]
    nectar = f["nectar"]
    return [
        QAItem(
            question="Where does the adventure happen?",
            answer=f"It happens at {world.setting.place}, where the animals and the path make a tiny mystery feel exciting.",
        ),
        QAItem(
            question=f"Who helped {child.id} solve the mystery?",
            answer=f"{friend.id} helped with calm steps, and together they solved it as a friendship story instead of a noisy one.",
        ),
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about the missing or misplaced nectar cup, which led them to look carefully instead of aggravating the animals.",
        ),
        QAItem(
            question=f"Why did {friend.id} tell {child.id} to slow down?",
            answer=f"{friend.id} wanted to be cautious so the animals would stay calm and the clue-search would not turn upsetting.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The nectar was back in place, the goat stayed calm, and {child.id} and {friend.id} ended with a gentle, friendly feeling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is nectar?",
            answer="Nectar is a sweet liquid that flowers make, and some insects and animals enjoy it as a treat.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking first so nobody gets hurt or startled.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people help each other, share ideas, and stay kind together.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def ASP_RULES() -> str:
    return r"""
valid_story(petting_zoo,mystery,nectar).
kind(adventure).
theme(friendship).
theme(caution).
theme(mystery).
ingredient(nectar).
place(petting_zoo).

solve_mystery(petting_zoo) :- valid_story(petting_zoo,mystery,nectar).
friendly(X) :- theme(friendship), solve_mystery(petting_zoo), X = child.
cautious(X) :- theme(caution), solve_mystery(petting_zoo), X = friend.
ok_story(P,A,N) :- valid_story(P,A,N), kind(adventure), theme(friendship), theme(caution).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for nid in PRIZES:
        lines.append(asp.fact("ingredient", nid))
    lines.append(asp.fact("kind", "adventure"))
    lines.append(asp.fact("theme", "friendship"))
    lines.append(asp.fact("theme", "caution"))
    lines.append(asp.fact("theme", "mystery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: petting-zoo mystery adventure with friendship and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = valid_combos()
    if args.place and args.place != "petting_zoo":
        raise StoryError("This world only supports the petting zoo setting.")
    if args.activity and args.activity != "mystery":
        raise StoryError("This world only supports a mystery-to-solve story.")
    if args.prize and args.prize != "nectar":
        raise StoryError("This world only supports nectar as the key object.")
    place, activity, prize = combos[0]
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell()
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


CURATED = [StoryParams(seed=274930118)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
