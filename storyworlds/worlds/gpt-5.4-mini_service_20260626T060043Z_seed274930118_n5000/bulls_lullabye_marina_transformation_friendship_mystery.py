#!/usr/bin/env python3
"""
Story world: bulls at a marina, a lullabye, a transformation, a friendship, and a gentle mystery.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    marina: str = "harbor marina"
    hero: str = "Nina"
    companion: str = "Toby"
    bull: str = "Brindle"
    seed: Optional[int] = None


MATERIALS = ("rope", "lantern", "bucket", "sailcloth")


@dataclass
class World:
    marina: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        return World(self.marina, copy.deepcopy(self.entities), [[]], dict(self.facts), set(self.fired))


def _narrate_name(entity: Entity) -> str:
    return entity.label or entity.id


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for bull in [e for e in world.entities.values() if e.type == "bull"]:
            if bull.meters.get("drowsy", 0) >= 1 and bull.meters.get("calmed", 0) < 1:
                sig = ("lullaby", bull.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    bull.meters["calmed"] = 1
                    bull.memes["peace"] = bull.memes.get("peace", 0) + 1
                    world.say(f"The soft lullabye settled over {_narrate_name(bull)} like moonlight on water.")
                    changed = True
        for hero in [e for e in world.entities.values() if e.kind == "character"]:
            if hero.memes.get("wonder", 0) >= 1 and hero.memes.get("friendship", 0) < 1:
                sig = ("friendship", hero.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    hero.memes["friendship"] = 1
                    world.say(f"{_narrate_name(hero)} stayed near the bull instead of running away, and that made a new friendship.")
                    changed = True
        for hero in [e for e in world.entities.values() if e.kind == "character"]:
            if hero.memes.get("curious", 0) >= 1 and hero.memes.get("mystery", 0) < 1:
                sig = ("mystery", hero.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    hero.memes["mystery"] = 1
                    world.say(f"Someone had moved the little harbor bell, and nobody knew why.")
                    changed = True
        for bull in [e for e in world.entities.values() if e.type == "bull"]:
            if bull.meters.get("calmed", 0) >= 1 and bull.meters.get("changed", 0) < 1:
                sig = ("transform", bull.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    bull.meters["changed"] = 1
                    bull.type = "gentle bull"
                    bull.label = f"gentle {bull.label}"
                    world.say(f"The bull was not wild anymore; it had become a gentle bull with slow eyes and a quiet step.")
                    changed = True


def tell(params: StoryParams) -> World:
    world = World(params.marina)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero, traits=["curious", "kind"]))
    companion = world.add(Entity(id=params.companion, kind="character", type="boy", label=params.companion, traits=["nervous", "loyal"]))
    bull = world.add(Entity(id=params.bull, kind="animal", type="bull", label=params.bull))
    note = world.add(Entity(id="note", kind="thing", type="note", label="a torn note", phrase="a torn note with wet ink"))
    note.owner = hero.id

    hero.memes["curious"] = 1
    hero.memes["wonder"] = 1

    world.say(f"At the {world.marina}, {hero.id} and {companion.id} found a quiet mystery beside the boats.")
    world.say(f"Under a dock lamp stood {bull.label}, a bull with a rope around one horn and sea spray on its hide.")
    world.say(f"{hero.id} noticed a torn note tucked under {note.phrase}, and the note mentioned a lullabye.")
    world.para()
    world.say(f"{companion.id} wanted to run, but {hero.id} listened. The harbor was full of fog, and the only clear sound was a soft hum.")
    world.say(f"{hero.id} began to sing a lullabye, low and steady, the kind that rocks dozing babies and sleepy kittens.")
    bull.meters["drowsy"] = 1
    propagate(world)
    world.para()
    world.say(f"Then {hero.id} and {companion.id} followed the clue to the old fish office, where a lantern glowed behind the glass.")
    world.say(f"They learned the bell had been moved so the boats would not wake the bull, and the bull had stayed calm because {hero.id} sang.")
    world.say(f"{companion.id} smiled at {hero.id} and said the mystery was not scary after all. It was a story about helping.")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly mystery story set at a marina that includes bulls and a lullabye.",
        f"Tell a gentle story about friendship, a bull, and a transformation at the {world.marina}.",
        "Write a short mystery where a song helps solve a problem and changes how someone feels.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["hero"]) if world.facts else None
    bull = world.get(world.facts["bull"]) if world.facts else None
    return [
        QAItem(
            question="Where did the mystery happen?",
            answer=f"It happened at the {world.marina}, near the boats and the dock lamp.",
        ),
        QAItem(
            question="What did the child sing?",
            answer="The child sang a lullabye, soft enough to calm the bull.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The bull changed from wild and worried into a gentle bull, and the children became friends with it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marina?",
            answer="A marina is a place where boats are kept, tied up, and cared for near the water.",
        ),
        QAItem(
            question="What is a lullabye?",
            answer="A lullabye is a soft song that helps someone relax or go to sleep.",
        ),
        QAItem(
            question="What is a bull?",
            answer="A bull is an adult male cow. Bulls can be strong and loud, but they can also become calm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- character(H).
bull(B) :- animal(B), bull_type(B).
drowsy_bull(B) :- bull(B), drowsy(B).
calmed(B) :- drowsy_bull(B), lullabye(S).
friendship(H,B) :- character(H), bull(B), calmed(B), kind(H).
transformed(B) :- bull(B), calmed(B).
mystery(H) :- character(H), clue(H), hidden_problem(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("character", "nina"),
        asp.fact("character", "toby"),
        asp.fact("animal", "brindle"),
        asp.fact("bull_type", "brindle"),
        asp.fact("clue", "nina"),
        asp.fact("hidden_problem", "nina"),
        asp.fact("lullabye", "song"),
        asp.fact("kind", "nina"),
        asp.fact("kind", "toby"),
        asp.fact("drowsy", "brindle"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show calmed/1.\n#show friendship/2.\n#show transformed/1.\n"))
    shown = set((s.name, len(s.arguments)) for s in model)
    need = {("calmed", 1), ("friendship", 2), ("transformed", 1)}
    if shown >= need:
        print("OK: ASP rules produce the expected story facts.")
        return 0
    print("MISMATCH: ASP rules did not produce expected facts.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A marina mystery about bulls, a lullabye, friendship, and transformation.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--marina", default="harbor marina")
    ap.add_argument("--hero", default=None)
    ap.add_argument("--companion", default=None)
    ap.add_argument("--bull", default=None)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Nina", "Mara", "Ivy", "Ada"])
    companion = args.companion or rng.choice(["Toby", "Eli", "Finn", "Owen"])
    bull = args.bull or rng.choice(["Brindle", "Patch", "Bramble", "Moss"])
    return StoryParams(marina=args.marina, hero=hero, companion=companion, bull=bull)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts = {"hero": params.hero, "companion": params.companion, "bull": params.bull}
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show calmed/1.\n#show friendship/2.\n#show transformed/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show calmed/1.\n#show friendship/2.\n#show transformed/1.\n"))
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams())]
    else:
        seen = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
