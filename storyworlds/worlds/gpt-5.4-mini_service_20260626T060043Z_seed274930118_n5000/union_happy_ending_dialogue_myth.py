#!/usr/bin/env python3
"""
storyworlds/worlds/union_happy_ending_dialogue_myth.py
=======================================================

A small mythic story world about a hard split that becomes a union through
conversation, shared labor, and a bright happy ending.

Premise:
- Two sides of a valley keep the old ways apart.
- A ritual must be completed, but neither side will begin alone.
- A child or young herald tries to speak for both sides.
- The split softens into a union, and the valley changes.

The simulated world tracks:
- a shared physical task in meters: carrying, tying, crossing, lighting
- emotional state in memes: pride, fear, trust, grief, hope, relief, joy
- dialogue-driven turns that can convert tension into agreement

The prose is authored from the state, not a frozen template.
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
    kind: str = "thing"      # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    side: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    setting: str = "the river gate"
    union_kind: str = "bridge"
    ritual: str = "wake the dawn"
    herald_name: str = "Mira"
    herald_type: str = "girl"
    left_name: str = "Alder"
    right_name: str = "Bram"
    seed: Optional[int] = None


SETTINGS = {
    "river_gate": "the river gate",
    "stone_hall": "the stone hall",
    "sun_terrace": "the sun terrace",
    "moon_path": "the moon path",
}

UNION_KINDS = {
    "bridge": {
        "label": "bridge",
        "physical": "tie the two bridge ropes together",
        "finish": "the bridge held steady over the river",
        "risk": "the rope ends would never meet",
    },
    "song": {
        "label": "song",
        "physical": "join the two chants into one song",
        "finish": "the shared song rose clear over the valley",
        "risk": "the old chants would stay split",
    },
    "torch": {
        "label": "torch",
        "physical": "touch the two flame-tips together",
        "finish": "the torch burned with one bright flame",
        "risk": "the light would stay divided",
    },
}

NAMES = ["Mira", "Nira", "Sela", "Tavi", "Kora", "Ilan", "Bren", "Jora", "Leto", "Rin"]
TYPES = ["girl", "boy"]
TITLES = ["elder", "herald", "messenger", "child", "priestess", "priest"]


ASP_RULES = r"""
% A union is possible when both sides are present and the ritual can be shared.
possible_union(S, U) :- setting(S), union_kind(U), has_left(S), has_right(S), shared_ritual(S, U).

% A union becomes happy when trust is enough and the shared act completes.
happy_union(S, U) :- possible_union(S, U), trust(S), completed(S, U).

#show possible_union/2.
#show happy_union/2.
"""


class ReasonableGate:
    @staticmethod
    def validate(params: StoryParams) -> None:
        if params.setting not in SETTINGS:
            raise StoryError("Unknown setting.")
        if params.union_kind not in UNION_KINDS:
            raise StoryError("Unknown union kind.")
        if not params.ritual.strip():
            raise StoryError("A ritual is required.")
        if not params.herald_name.strip():
            raise StoryError("A herald name is required.")


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for u in UNION_KINDS:
        lines.append(asp.fact("union_kind", u))
    for s in SETTINGS:
        lines.append(asp.fact("has_left", s))
        lines.append(asp.fact("has_right", s))
        for u in UNION_KINDS:
            lines.append(asp.fact("shared_ritual", s, u))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_possible_unions() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show possible_union/2."))
    return sorted(set(asp.atoms(model, "possible_union")))


def asp_happy_unions() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_union/2."))
    return sorted(set(asp.atoms(model, "happy_union")))


def asp_verify() -> int:
    py = {(s, u) for s in SETTINGS for u in UNION_KINDS}
    cl = set(asp_possible_unions())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} possible unions).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about a union and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--union-kind", choices=UNION_KINDS)
    ap.add_argument("--ritual")
    ap.add_argument("--herald-name")
    ap.add_argument("--herald-type", choices=TYPES)
    ap.add_argument("--left-name")
    ap.add_argument("--right-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    union_kind = args.union_kind or rng.choice(list(UNION_KINDS))
    herald_name = args.herald_name or rng.choice(NAMES)
    herald_type = args.herald_type or rng.choice(TYPES)
    left_name = args.left_name or rng.choice([n for n in NAMES if n != herald_name])
    right_name = args.right_name or rng.choice([n for n in NAMES if n not in {herald_name, left_name}])
    ritual = args.ritual or {
        "bridge": "bind the valley together",
        "song": "sing one voice across the divide",
        "torch": "bring the light to both sides",
    }[union_kind]
    params = StoryParams(setting=setting, union_kind=union_kind, ritual=ritual,
                         herald_name=herald_name, herald_type=herald_type,
                         left_name=left_name, right_name=right_name)
    ReasonableGate.validate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    union_def = UNION_KINDS[params.union_kind]

    herald = world.add(Entity(id=params.herald_name, kind="character", type=params.herald_type, label="herald"))
    left = world.add(Entity(id=params.left_name, kind="character", type="priest", label="left elder", side="left"))
    right = world.add(Entity(id=params.right_name, kind="character", type="priestess", label="right elder", side="right"))
    relic = world.add(Entity(id="relic", kind="thing", type=params.union_kind, label=union_def["label"], phrase=f"the old {union_def['label']}"))

    herald.memes.update({"hope": 1.0, "fear": 0.0, "trust": 0.0, "joy": 0.0})
    left.memes.update({"pride": 1.0, "fear": 0.5, "trust": 0.0, "grief": 0.0})
    right.memes.update({"pride": 1.0, "fear": 0.5, "trust": 0.0, "grief": 0.0})
    relic.meters.update({"broken": 1.0})

    world.facts.update(params=params, herald=herald, left=left, right=right, relic=relic, union_def=union_def)
    return world


def _raise_trust(ent: Entity, amount: float = 1.0) -> None:
    ent.memes["trust"] = ent.memes.get("trust", 0.0) + amount


def tell(params: StoryParams) -> World:
    world = build_world(params)
    herald = world.facts["herald"]
    left = world.facts["left"]
    right = world.facts["right"]
    union_def = world.facts["union_def"]

    world.say(f"At {world.setting}, two old sides of the valley faced each other in silence.")
    world.say(f"{herald.id} was a small {herald.type} who could hear what others would not say aloud.")
    world.say(f"On one side stood {left.id}, and on the other stood {right.id}; both kept the old split with heavy hearts.")

    world.para()
    world.say(f"The elders said the same thing in different voices: \"Not yet.\" \"Not without the other.\"")
    world.say(f"{herald.id} stepped between them and asked, \"What are you both afraid of?\"")
    left.memes["fear"] += 1.0
    right.memes["fear"] += 1.0
    world.say(f"{left.id} said, \"If we move first, our people may think we surrendered.\"")
    world.say(f"{right.id} answered, \"If we move first, our people may think we forgot our honor.\"")
    world.say(f"{herald.id} listened, and the listening itself made the air feel softer.")

    world.para()
    world.say(f"Then {herald.id} pointed to the {union_def['label']} and said, \"What if nobody moves first?\"")
    world.say(f"\"What if we {union_def['physical']} together?\"")
    _raise_trust(left, 1.0)
    _raise_trust(right, 1.0)
    left.memes["pride"] = max(0.0, left.memes.get("pride", 0.0) - 0.5)
    right.memes["pride"] = max(0.0, right.memes.get("pride", 0.0) - 0.5)
    world.say(f"{left.id} looked at {right.id}. {right.id} looked back. Neither found a sharper answer than the child's simple one.")

    world.para()
    world.say(f"\"Say it again,\" {left.id} whispered.")
    world.say(f"{herald.id} smiled and repeated, \"Together.\"")
    world.say(f"At once, {left.id} reached out, and {right.id} reached out too.")
    world.say(f"They {union_def['physical']}, and the long waiting ended.")

    left.memes["joy"] = left.memes.get("joy", 0.0) + 1.0
    right.memes["joy"] = right.memes.get("joy", 0.0) + 1.0
    herald.memes["joy"] = herald.memes.get("joy", 0.0) + 1.0
    herald.memes["trust"] = herald.memes.get("trust", 0.0) + 1.0
    world.facts["completed"] = True
    world.facts["trust"] = True

    world.para()
    if params.union_kind == "bridge":
        ending = "The bridge stood firm, and the river became a road instead of a wall."
    elif params.union_kind == "song":
        ending = "The shared song rose over the stones, and even the crows fell quiet to listen."
    else:
        ending = "The one bright flame pushed back the dark, and both sides warmed their hands at the same light."
    world.say(f"\"Now we are not two halves,\" {right.id} said.")
    world.say(f"\"Now we are one union,\" {left.id} answered.")
    world.say(f"{herald.id} laughed, and the valley remembered how to breathe again. {ending}")

    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short myth about a valley union using the word "union" and a happy ending.',
        f"Tell a child-friendly story where {p.herald_name} brings {p.left_name} and {p.right_name} into a union by dialogue.",
        f"Write a mythic tale at {p.setting.replace('_', ' ')} where a shared {p.union_kind} ends a split with kind words.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    herald = world.facts["herald"]
    left = world.facts["left"]
    right = world.facts["right"]
    union_def = world.facts["union_def"]

    return [
        QAItem(
            question=f"Who helped make the union happen at {world.setting}?",
            answer=f"{herald.id} helped by asking careful questions and leading both sides toward one shared choice."
        ),
        QAItem(
            question=f"What did {left.id} and {right.id} do together near the end?",
            answer=f"They {union_def['physical']} and finished the old split with one shared act."
        ),
        QAItem(
            question=f"Why did the story end happily?",
            answer=f"It ended happily because the two sides spoke honestly, trusted the herald, and joined in the union instead of staying apart."
        ),
        QAItem(
            question=f"What did the hero ask when the elders were still afraid?",
            answer=f"{herald.id} asked, 'What if nobody moves first?' and then offered a way to begin together."
        ),
        QAItem(
            question=f"What changed after the dialogue?",
            answer=f"Fear got smaller, trust grew, and the valley became a place where both sides could stand together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    if p.union_kind == "bridge":
        return [QAItem("What is a bridge for?", "A bridge helps people cross water or a gap so they can reach the other side.")]
    if p.union_kind == "song":
        return [QAItem("What is a song?", "A song is words and music joined together so people can sing them.")]
    return [QAItem("What is a torch?", "A torch is a light source that can burn brightly and help people see in the dark.")]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.side:
            bits.append(f"side={e.side}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(setting="river_gate", union_kind="bridge", herald_name="Mira", herald_type="girl", left_name="Alder", right_name="Bram"),
    StoryParams(setting="stone_hall", union_kind="song", herald_name="Tavi", herald_type="boy", left_name="Kora", right_name="Ilan"),
    StoryParams(setting="moon_path", union_kind="torch", herald_name="Sela", herald_type="girl", left_name="Rin", right_name="Jora"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, u) for s in SETTINGS for u in UNION_KINDS]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_union/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_possible_unions()
        print(f"{len(combos)} possible unions:")
        for s, u in combos:
            print(f"  {s:12} {u}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.herald_name}: {p.union_kind} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
