#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pooey_burrow_triumphant_seaside_promenade_conflict_mystery.py
=============================================================================================

A standalone story world for a small seaside mystery: a child notices a suspicious
mess at a promenade burrow, a conflict flares over what to do, clues are followed,
and a grown-up helps reveal the source so the ending feels triumphant.

Seed words: pooey, burrow, triumphant
Setting: seaside promenade
Style: mystery
Feature: conflict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "clues": 0.0, "calm": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "conflict": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class World:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class MysteryScene:
    id: str
    place: str
    description: str
    weird_sign: str
    clue_noun: str
    clue_action: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    effect: int
    action: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


SCENES = {
    "promenade": MysteryScene(
        "promenade",
        "the seaside promenade",
        "The seaside promenade glittered with wet boards, little lamps, and a salty wind.",
        "a weird pooey smell near a burrow beside the railing",
        "clue",
        "follow the smell",
        "a small seagull nest hidden in the burrow, with a broken snack box nearby",
        {"sea", "mystery", "burrow", "pooey", "promenade"},
    ),
}

RESPONSES = {
    "ask_guard": Response(
        "ask_guard", 3, 3,
        "asked the promenade guard for help and pointed to the clue",
        "asked for help, but the guard was too far away to notice in time",
        "asked the guard for help and pointed to the clue",
        {"help", "adult"},
    ),
    "follow_clue": Response(
        "follow_clue", 3, 2,
        "carefully followed the clue toward the burrow and found more clues",
        "followed the clue, but the path was too confusing and they got stuck",
        "carefully followed the clue toward the burrow",
        {"clue", "mystery"},
    ),
    "call_parent": Response(
        "call_parent", 3, 4,
        "called their parent right away and waited beside the lamps",
        "called for help, but no one answered quickly enough",
        "called their parent right away",
        {"help", "family"},
    ),
}

NAMES_GIRL = ["Mila", "Nora", "Ivy", "Lena", "Zoe", "Ava", "Maya"]
NAMES_BOY = ["Theo", "Noah", "Eli", "Milo", "Finn", "Leo", "Owen"]
TRAITS = ["curious", "careful", "brave", "thoughtful", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for scene in SCENES:
        for response in RESPONSES:
            out.append((scene, response))
    return out


def reasonableness_gate(scene: MysteryScene, response: Response) -> None:
    if response.sense < 2:
        raise StoryError("This response is too weak for a mystery conflict.")
    if "burrow" not in scene.tags:
        raise StoryError("The scene needs a burrow clue for this story.")
    if "pooey" not in scene.tags:
        raise StoryError("The scene needs the pooey smell to start the mystery.")


def outcome_of(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    return "triumphant" if response.effect >= 3 else "tangled"


def _follow_success(world: World, child: Entity, helper: Entity, scene: MysteryScene) -> None:
    child.meters["clues"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"At {scene.place}, {child.id} stopped short. "
        f"Near a low burrow, there was {scene.weird_sign}."
    )
    world.say(
        f'"{That is pooey," {helper.id} whispered, and {helper.pronoun()} '
        f"looked more closely at the clue."
    )


def _conflict(world: World, child: Entity, helper: Entity) -> None:
    child.memes["worry"] += 1
    helper.memes["conflict"] += 1
    world.say(
        f"{child.id} wanted to rush in, but {helper.id} wanted to be careful. "
        f"For a moment they disagreed and the windy promenade felt tense."
    )


def _reveal(world: World, scene: MysteryScene, parent: Entity, response: Response) -> None:
    world.say(
        f"Then {parent.label_word.capitalize()} came over, {response.action}, "
        f"and the mystery made sense."
    )
    world.say(
        f"Inside the burrow was {scene.reveal}. The pooey smell had led them "
        f"to the right spot all along."
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled, and the child stood a little taller, "
        f"feeling triumphant about solving the clue the safe way."
    )


def tell(scene: MysteryScene, response: Response, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, parent_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    world.facts.update(scene=scene, response=response, child=child, helper=helper, parent=parent)

    child.memes["curiosity"] = 2.0
    helper.memes["calm"] = 1.0

    world.say(
        f"One windy afternoon, {child.id} and {helper.id} walked along {scene.place}. "
        f"{scene.description}"
    )
    world.say(
        f"{child.id} noticed {scene.weird_sign}, and {helper.id} said they should not ignore it."
    )

    world.para()
    _follow_success(world, child, helper, scene)
    _conflict(world, child, helper)

    world.para()
    if response.id == "follow_clue":
        world.say(
            f"{helper.id} chose to {response.action}, and {child.id} stayed close by."
        )
    else:
        world.say(
            f"{child.id} listened and let {helper.id} {response.action}."
        )
    _reveal(world, scene, parent, response)

    child.memes["relief"] += 1
    child.meters["clues"] += 1
    world.facts["ending"] = "triumphant"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    return [
        f'Write a mystery story for a 3-to-5-year-old set at {scene.place} that includes the words "pooey", "burrow", and "triumphant".',
        f"Tell a seaside mystery where {f['child'].id} finds a pooey smell near a burrow, has a small conflict with {f['helper'].id}, and ends up triumphant.",
        f"Write a gentle conflict story with clues, lamps, and a hidden burrow on the promenade.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    scene = f["scene"]
    response = f["response"]
    return [
        QAItem(
            question="Where did the mystery happen?",
            answer=f"It happened at {scene.place}. The wet boards and salty wind made it feel like a real seaside mystery.",
        ),
        QAItem(
            question="What strange thing did they notice first?",
            answer=f"They noticed {scene.weird_sign}. That was the clue that made them stop and look more carefully.",
        ),
        QAItem(
            question=f"Why did {child.id} and {helper.id} disagree?",
            answer=f"{child.id} wanted to hurry forward, but {helper.id} wanted to be careful. They had a brief conflict because the clue looked strange and nobody wanted to make a mistake.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{parent.label_word.capitalize()} helped finish the search, and they found {scene.reveal}. The mystery turned triumphant because they solved it safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a burrow?",
            answer="A burrow is a hole or tunnel in the ground where a small animal might hide or rest.",
        ),
        QAItem(
            question="Why can a mystery feel exciting?",
            answer="A mystery feels exciting because there are clues to notice, questions to ask, and a surprise answer at the end.",
        ),
        QAItem(
            question="What does triumphant mean?",
            answer="Triumphant means feeling very proud and happy after something hard goes well.",
        ),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
scene(S) :- scene_fact(S).
response(R) :- response_fact(R).
valid(S, R) :- scene(S), response(R).
ending(triumphant) :- response_fact(R), effect(R, E), E >= 3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene_fact", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response_fact", rid))
        lines.append(asp.fact("effect", rid, r.effect))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program("", "#show ending/1."))
    atoms = asp.atoms(model, "ending")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: default/curated generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("promenade", "ask_guard", "Mira", "girl", "Jasper", "boy", "mother"),
    StoryParams("promenade", "follow_clue", "Theo", "boy", "Nina", "girl", "father"),
    StoryParams("promenade", "call_parent", "Ava", "girl", "Owen", "boy", "father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A seaside promenade mystery with conflict and a triumphant ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    scene = args.scene or "promenade"
    response = args.response or rng.choice(sorted(RESPONSES))
    reasonableness_gate(SCENES[scene], RESPONSES[response])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper_pool = [n for n in (NAMES_GIRL if helper_gender == "girl" else NAMES_BOY) if n != child]
    helper = args.helper or rng.choice(helper_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene, response, child, child_gender, helper, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], RESPONSES[params.response], params.child, params.child_gender,
                 params.helper, params.helper_gender, params.parent)
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
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos: {asp_valid_combos()}")
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
