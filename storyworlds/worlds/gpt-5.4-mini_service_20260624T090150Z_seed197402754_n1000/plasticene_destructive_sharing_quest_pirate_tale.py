#!/usr/bin/env python3
"""
A tiny Pirate Tale storyworld about a crew, a quest, and a plasticene treasure
that becomes destructive when one pirate tries to keep it all to themselves.
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


@dataclass
class Pirate:
    id: str
    kind: str = "character"
    role: str = "pirate"
    name: str = ""
    adjective: str = "brave"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def subject_verb(self, base: str) -> str:
        return base

    def ref(self) -> str:
        return self.name or self.id


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    crew_name: str
    pirate1: str
    pirate2: str
    treasure: str
    place: str
    seed: Optional[int] = None


CREWS = {
    "Captain's Cove": {
        "place": "the moonlit cove",
        "crew": ("Mara", "Finn"),
        "treasure": "plasticene compass",
    },
    "Barnacle Bay": {
        "place": "Barnacle Bay",
        "crew": ("Nell", "Rook"),
        "treasure": "plasticene star-map",
    },
    "Tidehook Isle": {
        "place": "Tidehook Isle",
        "crew": ("Pip", "Jory"),
        "treasure": "plasticene key",
    },
}

NAMES = ["Mara", "Finn", "Nell", "Rook", "Pip", "Jory", "Tessa", "Beck"]
ADJECTIVES = ["brave", "nimble", "cheery", "bold", "spry", "merry"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Pirate | Thing] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        for line in self.lines:
            if line == "":
                if out and out[-1] != "":
                    out.append("")
            else:
                out.append(line)
        return "\n".join(out).strip()


ASP_RULES = r"""
crew_member(X) :- pirate(X).
at_risk(T) :- treasure(T), plasticene(T).
destructive_horde(P,T) :- pirate(P), treasure(T), has(T,P), at_risk(T), selfish(P).
can_share(P,T) :- pirate(P), treasure(T), has(T,P), at_risk(T), not selfish(P).
resolved :- shared(T), treasure(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in ["pirate1", "pirate2"]:
        lines.append(asp.fact("pirate", pid))
    lines.append(asp.fact("treasure", "treasure"))
    lines.append(asp.fact("plasticene", "treasure"))
    lines.append(asp.fact("has", "pirate1", "treasure"))
    lines.append(asp.fact("selfish", "pirate1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combo(params: StoryParams) -> bool:
    return bool(params.crew_name in CREWS and params.pirate1 != params.pirate2)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate Tale storyworld: plasticene, destructive sharing, and a quest.")
    ap.add_argument("--crew-name", choices=CREWS.keys())
    ap.add_argument("--pirate1")
    ap.add_argument("--pirate2")
    ap.add_argument("--treasure")
    ap.add_argument("--place")
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
    crew_name = args.crew_name or rng.choice(list(CREWS))
    crew = CREWS[crew_name]
    pirate1 = args.pirate1 or crew["crew"][0]
    pirate2 = args.pirate2 or crew["crew"][1]
    if pirate1 == pirate2:
        raise StoryError("The crew needs two different pirates for a sharing quest.")
    treasure = args.treasure or crew["treasure"]
    place = args.place or crew["place"]
    return StoryParams(crew_name=crew_name, pirate1=pirate1, pirate2=pirate2, treasure=treasure, place=place)


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params):
        raise StoryError("That pirate tale combination does not make a sensible sharing quest.")
    world = World(params)
    p1 = world.add(Pirate(id="pirate1", name=params.pirate1, adjective="stubborn"))
    p2 = world.add(Pirate(id="pirate2", name=params.pirate2, adjective=random.choice(ADJECTIVES)))
    treasure = world.add(Thing(id="treasure", label=params.treasure, phrase=f"a stripy {params.treasure} made of plasticene"))
    treasure.owner = p1.id

    # Setup
    world.say(f"At {params.place}, {p1.ref()} and {p2.ref()} sailed with the crew of {params.crew_name}.")
    world.say(f"They had found {treasure.phrase}, and the shiny plasticene felt special in {p1.ref()}'s hands.")
    world.say(f"{p1.ref()} wanted to keep it all, even though the treasure was meant to guide a sharing quest.")

    # Turn
    world.para()
    p1.memes["greed"] = 1.0
    p1.memes["destructive"] = 1.0
    treasure.meters["bent"] = 1.0
    treasure.meters["split"] = 1.0
    world.say(f"But {p1.ref()} squeezed and pulled the plasticene too hard, and the treasure began to turn destructive.")
    world.say(f"It bent out of shape, and the quest map lost its clear path to the hidden cove.")

    # Resolution
    world.para()
    p2.memes["care"] = 1.0
    p2.memes["sharing"] = 1.0
    treasure.shared_with.add(p2.id)
    treasure.owner = "both"
    treasure.meters["fixed"] = 1.0
    p1.memes["greed"] = 0.0
    p1.memes["sharing"] = 1.0
    world.say(f"{p2.ref()} lifted the soft plasticene carefully and said, 'A quest is better when we share.'")
    world.say(f"Together they pressed it flat, joined the broken pieces, and made a new bright path.")
    world.say(f"By the end, the plasticene treasure was whole again, and the crew sailed on with both pirates smiling.")

    world.facts.update(
        p1=p1, p2=p2, treasure=treasure, params=params,
        shared=True, destructive=True, resolved=True
    )

    prompts = [
        f"Write a short Pirate Tale about {params.pirate1} and {params.pirate2} on a sharing quest with a plasticene treasure.",
        f"Tell a child-friendly pirate story where {params.pirate1} starts out destructive with {params.treasure}, then learns to share.",
        f"Write a simple sea adventure that includes the words plasticene, destructive, sharing, and quest.",
    ]

    story_qa = [
        QAItem(
            question=f"Who were the two pirates in the story?",
            answer=f"The story was about {params.pirate1} and {params.pirate2}, two pirates sailing together on {params.place}.",
        ),
        QAItem(
            question=f"What was the treasure made of?",
            answer=f"The treasure was made of plasticene, so it could be pressed, bent, and reshaped by careful hands.",
        ),
        QAItem(
            question=f"Why did the treasure get damaged at first?",
            answer=f"It got damaged because {params.pirate1} tried to keep it alone and squeezed it too hard, which made the treasure turn destructive and lose its shape.",
        ),
        QAItem(
            question=f"How did the pirates fix the problem?",
            answer=f"They shared the plasticene treasure, pressed it flat together, and made a new path for the quest.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is plasticene?",
            answer="Plasticene is a soft modeling material that can be pressed, shaped, and reshaped with your hands.",
        ),
        QAItem(
            question="What does destructive mean?",
            answer="Destructive means causing damage, breaking, or ruining something instead of helping it stay whole.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to find something, solve a problem, or reach an important goal.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, hold, or enjoy something together instead of keeping it all for yourself.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for ent in sample.world.entities.values():
            print(f"{ent.id}: {asdict(ent)}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: {asdict(ent)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(crew_name="Captain's Cove", pirate1="Mara", pirate2="Finn", treasure="plasticene compass", place="the moonlit cove"),
    StoryParams(crew_name="Barnacle Bay", pirate1="Nell", pirate2="Rook", treasure="plasticene star-map", place="Barnacle Bay"),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show crew_member/1. #show destructive_horde/2. #show can_share/2. #show resolved/0.")
    model = asp.one_model(program)
    shown = {str(a) for a in model}
    if shown:
        print("OK: ASP program solved with a model.")
        return 0
    print("No ASP model produced.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show crew_member/1. #show destructive_horde/2. #show can_share/2. #show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show crew_member/1. #show destructive_horde/2. #show can_share/2. #show resolved/0."))
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
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
                params.seed = base_seed + i
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
            header = f"### {p.crew_name} — {p.pirate1} and {p.pirate2}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
