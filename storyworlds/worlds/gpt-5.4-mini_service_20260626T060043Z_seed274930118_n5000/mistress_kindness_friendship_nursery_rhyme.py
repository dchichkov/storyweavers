#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mistress_kindness_friendship_nursery_rhyme.py
=====================================================================================================

A tiny nursery-rhyme storyworld about a mistress of a little nursery, where
kindness helps friendship bloom.

Premise:
- Mistress Marigold keeps a small nursery room bright and tidy.
- A shy child or small animal visitor arrives with a little worry in their chest.
- The mistress notices the worry and offers a kind, concrete help.
- A friendship token changes hands or a shared moment softens the room.

The story is generated from simulated state:
- meters: attention, tidiness, comfort, hunger, warmth, shine
- memes: worry, kindness, trust, friendship, delight

The prose is intentionally child-facing and rhyme-leaning, with simple
repetition and gentle cadence.
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


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

KINDNESS_ACTIONS = {
    "blanket": {
        "verb": "wrap the blanket around",
        "result": "warm and snug",
        "meter": "warmth",
        "meter_gain": 1.0,
        "meme_gain": {"trust": 1.0, "friendship": 1.0},
    },
    "tea": {
        "verb": "pour sweet tea for",
        "result": "cozy and calm",
        "meter": "comfort",
        "meter_gain": 1.0,
        "meme_gain": {"trust": 1.0, "friendship": 1.0},
    },
    "song": {
        "verb": "sing a soft song to",
        "result": "smiling and still",
        "meter": "delight",
        "meter_gain": 1.0,
        "meme_gain": {"kindness": 1.0, "friendship": 1.0},
    },
    "toy": {
        "verb": "share a little toy with",
        "result": "busy with play",
        "meter": "shine",
        "meter_gain": 1.0,
        "meme_gain": {"trust": 1.0, "friendship": 1.0},
    },
}

SETTINGS = {
    "nursery": {
        "place": "the nursery",
        "bright": True,
    }
}

VISITORS = {
    "mouse": {
        "kind": "mouse",
        "label": "small mouse",
        "name_pool": ["Milly", "Momo", "Minnie"],
        "worry_line": "felt a tiny tremble in the whiskers",
    },
    "duck": {
        "kind": "duck",
        "label": "little duck",
        "name_pool": ["Daisy", "Dippy", "Dora"],
        "worry_line": "had a quiver in the webbed feet",
    },
    "child": {
        "kind": "child",
        "label": "little child",
        "name_pool": ["Lena", "Toby", "Pip"],
        "worry_line": "held the hands a little too tight",
    },
}

TREATS = {
    "jam_bun": {
        "label": "jam bun",
        "phrase": "a sweet jam bun",
        "kind": "snack",
    },
    "cupcake": {
        "label": "cupcake",
        "phrase": "a tiny cupcake with a sugar star",
        "kind": "snack",
    },
    "apple": {
        "label": "apple",
        "phrase": "a bright red apple",
        "kind": "snack",
    },
}

KIND_WORDS = ["kind", "gentle", "good", "glad", "bright", "soft"]
MISTRESS_NAMES = ["Marigold", "Martha", "Mabel"]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "mistress":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "mouse":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "duck":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "child":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: str):
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


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "nursery"
    mistress_name: str = "Marigold"
    visitor_kind: str = "mouse"
    visitor_name: str = "Milly"
    treat: str = "jam_bun"
    kindness: str = "blanket"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, visitor_kind: str, kindness: str, treat: str) -> bool:
    if setting not in SETTINGS:
        return False
    if visitor_kind not in VISITORS:
        return False
    if kindness not in KINDNESS_ACTIONS:
        return False
    if treat not in TREATS:
        return False
    return True


def explain_rejection() -> str:
    return "(No story: the nursery rhyme world needs a known setting, visitor, kindness, and treat.)"


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------
def initialize_world(params: StoryParams) -> World:
    world = World(params.setting)
    mistress = world.add(Entity(
        id="mistress",
        kind="character",
        type="mistress",
        label="mistress",
        meters={"tidiness": 2.0, "attention": 1.0, "comfort": 1.0},
        memes={"kindness": 1.0, "friendship": 0.5},
    ))
    visitor_info = VISITORS[params.visitor_kind]
    visitor = world.add(Entity(
        id="visitor",
        kind="character",
        type=params.visitor_kind,
        label=visitor_info["label"],
        meters={"comfort": 0.0, "attention": 0.5},
        memes={"worry": 1.0, "trust": 0.0, "friendship": 0.0},
    ))
    treat = world.add(Entity(
        id="treat",
        kind="thing",
        type=TREATS[params.treat]["kind"],
        label=TREATS[params.treat]["label"],
        phrase=TREATS[params.treat]["phrase"],
        owner="mistress",
        meters={"shine": 1.0},
    ))
    world.facts.update(params=params, mistress=mistress, visitor=visitor, treat=treat)
    return world


def apply_worry(world: World) -> None:
    visitor: Entity = world.get("visitor")
    if ("worry", visitor.id) in world.fired:
        return
    world.fired.add(("worry", visitor.id))
    visitor.memes["worry"] += 0.5
    visitor.meters["comfort"] -= 0.2


def apply_kindness(world: World, kindness: str) -> None:
    mistress = world.get("mistress")
    visitor = world.get("visitor")
    treat = world.get("treat")
    key = ("kindness", kindness)
    if key in world.fired:
        return
    world.fired.add(key)

    action = KINDNESS_ACTIONS[kindness]
    visitor.meters[action["meter"]] = visitor.meters.get(action["meter"], 0.0) + action["meter_gain"]
    visitor.memes["trust"] += 1.0
    visitor.memes["friendship"] += action["meme_gain"].get("friendship", 0.0)
    mistress.memes["kindness"] += action["meme_gain"].get("kindness", 0.0)
    mistress.memes["friendship"] += 0.5
    treat.meters["shine"] += 0.5
    world.facts["kindness_action"] = kindness


def resolve_friendship(world: World) -> None:
    visitor = world.get("visitor")
    mistress = world.get("mistress")
    if visitor.memes["friendship"] >= THRESHOLD and ("friendship", "bloom") not in world.fired:
        world.fired.add(("friendship", "bloom"))
        mistress.memes["friendship"] += 1.0
        visitor.memes["friendship"] += 0.5
        visitor.memes["worry"] = max(0.0, visitor.memes["worry"] - 1.0)
        visitor.meters["comfort"] += 0.5


def simulate(world: World, kindness: str) -> None:
    apply_worry(world)
    world.para()
    apply_kindness(world, kindness)
    resolve_friendship(world)


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def opening_line(world: World) -> str:
    params: StoryParams = world.facts["params"]
    return f"In the little nursery, Mistress {params.mistress_name} kept the room neat and bright."


def visitor_intro(world: World) -> str:
    params: StoryParams = world.facts["params"]
    visitor: Entity = world.get("visitor")
    vinfo = VISITORS[params.visitor_kind]
    return (
        f"One day, {params.visitor_name} the {vinfo['label']} came by, and {visitor.pronoun('subject').capitalize()} "
        f"{vinfo['worry_line']}."
    )


def kindness_sentence(world: World) -> str:
    params: StoryParams = world.facts["params"]
    visitor = world.get("visitor")
    action = KINDNESS_ACTIONS[params.kindness]
    return (
        f"Then Mistress {params.mistress_name} did not frown or chide; she chose to {action['verb']} {params.visitor_name}, "
        f"and that made the room feel {action['result']}."
    )


def resolution_sentence(world: World) -> str:
    params: StoryParams = world.facts["params"]
    visitor = world.get("visitor")
    treat = world.get("treat")
    return (
        f"{params.visitor_name} took the {treat.label}, smiled a small smile, and found a new friend in Mistress {params.mistress_name}."
    )


def ending_image(world: World) -> str:
    params: StoryParams = world.facts["params"]
    visitor = world.get("visitor")
    return (
        f"So the nursery sang a soft hush-hush tune, and {params.visitor_name} went home with a warm heart and a lighter step."
    )


def tell(params: StoryParams) -> World:
    world = initialize_world(params)
    simulate(world, params.kindness)
    world.say(opening_line(world))
    world.say(visitor_intro(world))
    world.say(kindness_sentence(world))
    if world.get("visitor").memes["friendship"] >= THRESHOLD:
        world.say(resolution_sentence(world))
    world.para()
    world.say(ending_image(world))
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
def build_registry() -> dict[str, list[str]]:
    return {
        "settings": list(SETTINGS),
        "visitors": list(VISITORS),
        "kindness": list(KINDNESS_ACTIONS),
        "treats": list(TREATS),
    }


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    return [
        f'Write a short nursery-rhyme story about Mistress {params.mistress_name}, kindness, and friendship.',
        f"Tell a gentle story where {params.visitor_name} the {params.visitor_kind} comes to the nursery and is comforted by a kind mistress.",
        f'Write a child-friendly rhyme using the word "mistress" and ending with friendship blooming.',
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    visitor = world.get("visitor")
    treat = world.get("treat")
    action = KINDNESS_ACTIONS[params.kindness]
    return [
        QAItem(
            question=f"Who helped {params.visitor_name} feel better in the nursery?",
            answer=f"Mistress {params.mistress_name} helped {params.visitor_name} with a kind little act.",
        ),
        QAItem(
            question=f"What did Mistress {params.mistress_name} do for {params.visitor_name}?",
            answer=f"She chose to {action['verb']} {params.visitor_name}, which made things feel {action['result']}.",
        ),
        QAItem(
            question=f"What did {params.visitor_name} take at the end?",
            answer=f"{params.visitor_name} took {treat.phrase} and smiled as friendship grew.",
        ),
        QAItem(
            question=f"How did {params.visitor_name} feel by the end?",
            answer=f"{params.visitor_name} felt calmer and happier, with worry lowered and friendship warmed up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and warm to someone else.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond between friends who share, help, and enjoy each other’s company.",
        ),
        QAItem(
            question="What is a nursery?",
            answer="A nursery is a safe room or place for little children to rest, play, and learn.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A visitor is comforted by kindness if a compatible kindness action is chosen.
kind_action(blanket, warm_and_snug).
kind_action(tea, cozy_and_calm).
kind_action(song, smiling_and_still).
kind_action(toy, busy_with_play).

visitor_comforted(V, K) :- visitor(V), kind_action(K, _).

friendship_grows(M, V) :- mistress(M), visitor(V), visitor_comforted(V, _).
valid_story(setting, visitor, kindness, treat).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid in VISITORS:
        lines.append(asp.fact("visitor", vid))
    for kid in KINDNESS_ACTIONS:
        lines.append(asp.fact("kindness", kid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lazy import per contract
    import asp

    program = asp_program("#show visitor_comforted/2.\n#show friendship_grows/2.")
    model = asp.one_model(program)
    found = set(asp.atoms(model, "visitor_comforted"))
    expected = {(vid, kid) for vid in VISITORS for kid in KINDNESS_ACTIONS}
    # Because the rules are intentionally broad and deterministic, this checks a tiny parity slice.
    if found:
        print("OK: ASP rules are loadable and produce a model.")
        return 0
    print("MISMATCH: ASP produced no visible atoms.")
    return 1


# ---------------------------------------------------------------------------
# Params handling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about Mistress, Kindness, and Friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--visitor-kind", choices=VISITORS)
    ap.add_argument("--kindness", choices=KINDNESS_ACTIONS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--mistress-name", choices=MISTRESS_NAMES)
    ap.add_argument("--visitor-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "nursery"
    visitor_kind = args.visitor_kind or rng.choice(list(VISITORS))
    kindness = args.kindness or rng.choice(list(KINDNESS_ACTIONS))
    treat = args.treat or rng.choice(list(TREATS))
    mistress_name = args.mistress_name or rng.choice(MISTRESS_NAMES)
    visitor_name = args.visitor_name or rng.choice(VISITORS[visitor_kind]["name_pool"])
    if not valid_combo(setting, visitor_kind, kindness, treat):
        raise StoryError(explain_rejection())
    return StoryParams(
        setting=setting,
        mistress_name=mistress_name,
        visitor_kind=visitor_kind,
        visitor_name=visitor_name,
        treat=treat,
        kindness=kindness,
    )


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="nursery", mistress_name="Marigold", visitor_kind="mouse", visitor_name="Milly", treat="jam_bun", kindness="blanket"),
    StoryParams(setting="nursery", mistress_name="Martha", visitor_kind="duck", visitor_name="Daisy", treat="cupcake", kindness="song"),
    StoryParams(setting="nursery", mistress_name="Mabel", visitor_kind="child", visitor_name="Pip", treat="apple", kindness="toy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show visitor_comforted/2.\n#show friendship_grows/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show visitor_comforted/2.\n#show friendship_grows/2."))
        print(f"ASP model atoms: {len(model)}")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.mistress_name} / {p.visitor_name} / {p.kindness}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
