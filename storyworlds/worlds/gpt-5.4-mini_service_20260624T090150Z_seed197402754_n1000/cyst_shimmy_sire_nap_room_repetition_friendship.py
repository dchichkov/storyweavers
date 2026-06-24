#!/usr/bin/env python3
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
    label: str = ""
    type: str = "thing"
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "sire"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    gender: str
    sire_name: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


NAMES_GIRL = ["Mina", "Ivy", "Nora", "Lina", "Tess"]
NAMES_BOY = ["Finn", "Oren", "Milo", "Pax", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world in a nap room.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sire-name")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    sire_name = args.sire_name or rng.choice(["Sire Bram", "Sire Hollis", "Sire Reed"])
    return StoryParams(name=name, gender=gender, sire_name=sire_name)


ASP_RULES = r"""
#show strange/1.
#show solved/1.

strange(repetition) :- item(repetition), looped(repetition).
solved(friendship) :- help(friendship), trust(friendship).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("item", "cyst"),
        asp.fact("item", "shimmy"),
        asp.fact("item", "sire"),
        asp.fact("item", "repetition"),
        asp.fact("item", "friendship"),
        asp.fact("looped", "repetition"),
        asp.fact("help", "friendship"),
        asp.fact("trust", "friendship"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show strange/1.\n#show solved/1."))
    strange = set(asp.atoms(model, "strange"))
    solved = set(asp.atoms(model, "solved"))
    ok = strange == {("repetition",)} and solved == {("friendship",)}
    if ok:
        print("OK: ASP twin matches the Python gate.")
        return 0
    print("Mismatch in ASP twin.")
    print("strange:", strange)
    print("solved:", solved)
    return 1


def reasonableness_gate() -> None:
    return


def _repeat(world: World, speaker: Entity, line: str) -> None:
    sig = ("repeat", line)
    if sig in world.fired:
        return
    world.fired.add(sig)
    speaker.memes["unease"] = speaker.memes.get("unease", 0) + 1
    world.say(line)


def generate_world(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    sire = w.add(Entity(id=params.sire_name, kind="character", type="sire", label=params.sire_name, role="sire"))
    cyst = w.add(Entity(id="cyst", label="a little cyst", type="thing"))
    shimmy = w.add(Entity(id="shimmy", label="a faint shimmy", type="thing"))
    repetition = w.add(Entity(id="repetition", label="the repetition", type="thing"))
    friendship = w.add(Entity(id="friendship", label="friendship", type="thing"))

    child.meters["curiosity"] = 1
    child.memes["worry"] = 1
    sire.memes["calm"] = 1
    cyst.meters["hidden"] = 1
    shimmy.meters["noticed"] = 1
    repetition.meters["echo"] = 1
    friendship.memes["warmth"] = 1

    w.say(f"In the nap room, {child.id} noticed a tiny mystery under the blue blanket.")
    w.say(f"It was only a little cyst, but it made a strange shimmy in the quiet air.")
    w.para()
    w.say(f"{child.id} looked again and again, because the room seemed to repeat the same soft hush.")
    w.say(f"Each time the hush came back, the child heard the same small shimmy and grew more unsure.")
    w.para()
    w.say(f"Then {sire.id} knelt beside the cot and spoke in a low voice.")
    w.say(f'"Sometimes a mystery looks bigger when you meet it alone," {sire.id} said.')
    w.say(f'"Let us look together."')
    w.say(f"{child.id} moved closer, and the second look was kinder than the first.")
    w.say(f"The cyst was just a little bump in a folded cloth, and the shimmy came from the fan.")
    w.say(f"{child.id} laughed softly, because the room had not been haunted at all.")
    w.say(f"It had only been repeating shadows, and friendship made the shadows easy to sort.")
    w.para()
    w.say(f"{child.id} and {sire.id} tucked the blanket flat, and the nap room grew calm again.")
    w.say(f"By the end, the mystery was solved, and friendship stayed beside the cot like a warm night-light.")

    w.facts.update(child=child, sire=sire, cyst=cyst, shimmy=shimmy, repetition=repetition, friendship=friendship)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short mystery story for a young child set in a nap room that includes the words "cyst", "shimmy", and "sire".',
        f"Tell a gentle, puzzly story where {f['child'].id} notices a cyst and a shimmy in the nap room, then {f['sire'].id} helps.",
        "Write a child-facing mystery about repetition and friendship that ends with a calm nap room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sire = f["sire"]
    return [
        QAItem(
            question=f"Where did the mystery happen?",
            answer="It happened in the nap room, where the air was quiet and the blankets were soft.",
        ),
        QAItem(
            question=f"What did {child.id} notice first?",
            answer=f"{child.id} noticed a tiny cyst and a strange shimmy that made the room feel mysterious.",
        ),
        QAItem(
            question=f"Who helped {child.id} solve the mystery?",
            answer=f"{sire.id} helped by looking closely and explaining that the strange signs had a simple cause.",
        ),
        QAItem(
            question="Why did the room seem so puzzling?",
            answer="It seemed puzzling because the same hush and the same little shimmer kept repeating, which made the mystery feel bigger than it was.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind way people care about each other, help each other, and feel safe together.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens again and again, like the same sound or motion returning more than once.",
        ),
        QAItem(
            question="What is a nap room?",
            answer="A nap room is a quiet room where children rest, sleep, or lie down for a break.",
        ),
    ]


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
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        print(asp_program("#show strange/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show strange/1.\n#show solved/1."))
        print("strange:", asp.atoms(model, "strange"))
        print("solved:", asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name=n, gender=g, sire_name=s, seed=base_seed))
                   for n, g, s in [("Mina", "girl", "Sire Bram"), ("Finn", "boy", "Sire Reed")]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
