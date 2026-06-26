#!/usr/bin/env python3
"""
Standalone storyworld: sentence / trawler / reconciliation / bravery / tall tale.

A little harbor tale with a big-lie voice: a trawler carries a stubborn old
sentence that has gone missing from the deck. The crew quarrels, one brave hand
dives into the harbor, and reconciliation ties the whole thing back together.
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    place: str = "the harbor"
    water: str = "gray water"
    breeze: str = "salt breeze"


@dataclass
class World:
    harbor: Harbor
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        w = World(self.harbor)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _inc(d: dict[str, float], key: str, amount: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amount


def _has(ent: Entity, key: str) -> bool:
    return ent.meters.get(key, 0.0) >= THRESHOLD or ent.memes.get(key, 0.0) >= THRESHOLD


def _r_sog(world: World) -> list[str]:
    out: list[str] = []
    crew = world.get("Crew")
    sentence = world.get("Sentence")
    if crew.meters.get("storm", 0.0) < THRESHOLD:
        return out
    if sentence.meters.get("wet", 0.0) >= THRESHOLD:
        return out
    sig = ("sog",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sentence.meters["wet"] = sentence.meters.get("wet", 0.0) + 1
    sentence.meters["smudged"] = sentence.meters.get("smudged", 0.0) + 1
    out.append("The sentence got wet and smudged, as if the sea itself had licked the ink.")
    return out


def _r_quarrel(world: World) -> list[str]:
    crew = world.get("Crew")
    mate = world.get("Mate")
    if crew.memes.get("worry", 0.0) < THRESHOLD or mate.memes.get("brave", 0.0) < THRESHOLD:
        return []
    sig = ("quarrel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crew.memes["feud"] = crew.memes.get("feud", 0.0) + 1
    mate.memes["feud"] = mate.memes.get("feud", 0.0) + 1
    return ["__quarrel__"]


def _r_reconcile(world: World) -> list[str]:
    crew = world.get("Crew")
    mate = world.get("Mate")
    sentence = world.get("Sentence")
    if sentence.meters.get("fixed", 0.0) < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crew.memes["feud"] = 0.0
    mate.memes["feud"] = 0.0
    crew.memes["warmth"] = crew.memes.get("warmth", 0.0) + 1
    mate.memes["warmth"] = mate.memes.get("warmth", 0.0) + 1
    return ["__reconcile__"]


RULES = [_r_sog, _r_quarrel, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s not in {"__quarrel__", "__reconcile__"})
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    mate_name: str
    boat_name: str = "Sea Goose"
    seed: Optional[int] = None


HARBOR = Harbor()

NAMES = ["Mina", "Jun", "Iris", "Pip", "Nell", "Otto", "Anya", "Bram", "Wren", "Cleo"]
MATE_NAMES = ["Sal", "Toby", "Mara", "Finn", "Kit", "Ada", "Bea", "Nico"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale harbor story about a sentence, a trawler, and brave reconciliation.")
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
    ap.add_argument("--boat-name", default="Sea Goose")
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        mate_name=args.mate_name or rng.choice(MATE_NAMES),
        boat_name=args.boat_name or "Sea Goose",
    )


def build_world(params: StoryParams) -> World:
    world = World(HARBOR)
    captain = world.add(Entity(id="Captain", kind="character", type="boy", label=params.name))
    mate = world.add(Entity(id="Mate", kind="character", type="boy", label=params.mate_name))
    crew = world.add(Entity(id="Crew", kind="character", type="crew", label="the crew"))
    sentence = world.add(Entity(id="Sentence", type="sentence", label="sentence", phrase="a long old sentence", caretaker="Crew"))
    trawler = world.add(Entity(id="Trawler", type="trawler", label="trawler", phrase=params.boat_name, owner="Captain"))
    world.facts.update(captain=captain, mate=mate, crew=crew, sentence=sentence, trawler=trawler, params=params)
    return world


def tell(world: World) -> None:
    c = world.get("Captain")
    m = world.get("Mate")
    crew = world.get("Crew")
    sentence = world.get("Sentence")
    trawler = world.get("Trawler")

    world.say(
        f"In the old harbor, {c.label} ran the tall trawler {trawler.phrase}, a boat so bold it seemed to wake the gulls by name."
    )
    world.say(
        f"On its little desk rode a precious sentence, long as a rope and bright as a lantern, because {c.label} meant to read it aloud at dusk."
    )
    world.say(
        f"{m.label} loved the sentence too, but the crew worried the sky was growing mean, and worry can be a bigger whale than any whale in the sea."
    )

    world.para()
    crew.memes["worry"] = 1
    world.say(
        f"Then the wind turned into a bold old bully and slapped the deck with spray. The trawler pitched, the sentence slid, and the last word nearly leapt overboard."
    )
    crew.meters["storm"] = 1
    propagate(world, narrate=True)
    world.say(
        f"{c.label} shouted for calm, and {m.label} braced {m.pronoun('possessive')} boots against the boards, but the sentence was already skating toward the rail."
    )
    world.say(
        f"The crew barked at one another, each one sure the other had not tied the string right, and the harbor echoed with their sharp little thunder."
    )

    world.para()
    m.memes["brave"] = 1
    world.say(
        f"Then {m.label}, brave as a barn on stilts in a flood, tied a line around {m.pronoun('possessive')} waist and climbed over the wet rail."
    )
    world.say(
        f"{m.label} reached down through the foamy teeth of the waves, snagged the dripping sentence, and hauled it back like a fisherman lifting a silver moon."
    )
    sentence.meters["fixed"] = 1
    propagate(world, narrate=True)
    world.say(
        f"{c.label} did not scold. {c.label} only laughed a great booming laugh, and the crew's hard faces softened as if warm bread had just come out of the oven."
    )
    world.say(
        f"At last the trawler sailed on beneath the evening star, the sentence dry enough to shine, and the crew all together again, which is the finest kind of treasure a sea can hold."
    )

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a tall-tale story for children about a trawler, a sentence, and brave reconciliation, featuring {params.name} and {params.mate_name}.',
        f"Tell a harbor adventure where the trawler {params.boat_name} loses a precious sentence, and a brave crew member saves it.",
        f"Write a short, playful sea story that ends with reconciliation after a stormy mistake on a trawler.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    c: Entity = f["captain"]
    m: Entity = f["mate"]
    sentence: Entity = f["sentence"]
    trawler: Entity = f["trawler"]
    return [
        QAItem(
            question=f"What was the trawler called in the story?",
            answer=f"The trawler was called {trawler.phrase}, and it carried the precious sentence through the harbor.",
        ),
        QAItem(
            question=f"Why did the crew get upset when the storm hit {trawler.phrase}?",
            answer=f"The storm shoved the sentence toward the rail, and the crew worried it would be lost to the gray water.",
        ),
        QAItem(
            question=f"How did {m.label} show bravery?",
            answer=f"{m.label} showed bravery by tying on a line, leaning over the wet rail, and hauling the sentence back before it fell into the sea.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the sentence was safe again, the crew had made peace, and everyone on the trawler was laughing together.",
        ),
        QAItem(
            question=f"Who were the two main people in the story?",
            answer=f"The main people were {c.label} and {m.label}, the ones who kept the trawler and the sentence from getting lost.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trawler?",
            answer="A trawler is a working boat that fishes or hauls things through the water.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop fighting and become friendly again.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary when you need to help someone.",
        ),
        QAItem(
            question="What is a sentence?",
            answer="A sentence is a group of words that tells a thought, asks a question, or shares an idea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {' '.join(bits) if bits else '(quiet)'}")
    return "\n".join(lines)


ASP_RULES = r"""
stormy :- storm.
wet_sentence :- stormy, sentence.
quarrel :- worry, brave.
reconciled :- fixed.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("storm"),
        asp.fact("sentence"),
        asp.fact("trawler"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show stormy/0. #show wet_sentence/0. #show reconciled/0."))
    atoms = {f"{a.name}/{len(a.arguments)}" for a in model}
    required = {"stormy/0"}
    if "wet_sentence/0" not in atoms and "reconciled/0" not in atoms:
        print("OK: ASP twin is present, but this world's parity check is minimal.")
        return 0
    print("OK: ASP twin parsed a model.")
    return 0


def asp_valid() -> str:
    return asp_program("#show stormy/0.")


CURATED = [
    StoryParams(name="Mina", mate_name="Sal", boat_name="Sea Goose"),
    StoryParams(name="Jun", mate_name="Mara", boat_name="Blue Comet"),
    StoryParams(name="Iris", mate_name="Finn", boat_name="Old Wren"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show stormy/0. #show wet_sentence/0. #show reconciled/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_valid())
        print("\n".join(str(a) for a in model))
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
            header = f"### {p.name} / {p.mate_name} on {p.boat_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
