#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/yacht_snout_magic_fairy_tale.py
============================================================================================================

A tiny fairy-tale story world about a magical yacht, a curious snout charm,
and a small trouble that turns into a gentle resolution.

The domain is built from the seed words:
- yacht
- snout

Style:
- Fairy tale
- Child-facing
- Small, concrete, state-driven
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
    attrs: dict[str, str] = field(default_factory=dict)
    magic: bool = False
    can_sail: bool = False
    has_snout: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def title(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    ship_name: str
    charm_name: str
    magic_kind: str
    trouble: str
    ending: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


HEROES = [("Anya", "girl"), ("Bram", "boy"), ("Cleo", "girl"), ("Dorian", "boy"), ("Elsa", "girl")]
HELPERS = [("Milo", "boy"), ("Nina", "girl"), ("Pip", "boy"), ("Rosie", "girl")]
SHIP_NAMES = ["Pearl Yacht", "Moon Yacht", "Little Yacht", "Star Yacht"]
CHARMS = ["snout charm", "golden snout", "snout pebble", "snout shell"]
MAGIC_KINDS = ["gentle magic", "moon magic", "tide magic", "kind magic"]
TROUBLES = ["a fog wall", "a sleepy wind", "a tangled rope", "a shy wave"]
ENDINGS = ["sailed safely home", "glided into harbor", "found the bright shore", "returned under starlight"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale world with a yacht, a snout, and magic.")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--ship-name")
    ap.add_argument("--charm-name")
    ap.add_argument("--magic-kind")
    ap.add_argument("--trouble")
    ap.add_argument("--ending")
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
    hero, hero_type = rng.choice(HEROES) if not args.hero else next((h, t) for h, t in HEROES if h == args.hero)
    helper, helper_type = rng.choice(HELPERS) if not args.helper else next((h, t) for h, t in HELPERS if h == args.helper)
    return StoryParams(
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        ship_name=args.ship_name or rng.choice(SHIP_NAMES),
        charm_name=args.charm_name or rng.choice(CHARMS),
        magic_kind=args.magic_kind or rng.choice(MAGIC_KINDS),
        trouble=args.trouble or rng.choice(TROUBLES),
        ending=args.ending or rng.choice(ENDINGS),
    )


def _setup(world: World, p: StoryParams) -> None:
    hero = world.add(Entity(id=p.hero, kind="character", type=p.hero_type, role="hero"))
    helper = world.add(Entity(id=p.helper, kind="character", type=p.helper_type, role="helper"))
    yacht = world.add(Entity(id="yacht", kind="thing", type="yacht", label=p.ship_name, can_sail=True, magic=True))
    snout = world.add(Entity(id="snout", kind="thing", type="charm", label=p.charm_name, has_snout=True, magic=True))
    sky = world.add(Entity(id="sky", kind="thing", type="sky", label="the moonlit sky"))
    world.facts.update(hero=hero, helper=helper, yacht=yacht, snout=snout, sky=sky, params=p)
    hero.memes["hope"] = 1.0
    helper.memes["curiosity"] = 1.0
    yacht.meters["stillness"] = 1.0
    yacht.meters["magic"] = 1.0
    snout.meters["glow"] = 1.0


def _apply_magic(world: World) -> None:
    if "magic" in world.fired:
        return
    world.fired.add("magic")
    y = world.get("yacht")
    s = world.get("snout")
    y.meters["stillness"] = max(0.0, y.meters["stillness"] - 1.0)
    y.meters["motion"] = y.meters.get("motion", 0.0) + 1.0
    s.memes["warmth"] = s.memes.get("warmth", 0.0) + 1.0


def tell(world: World, p: StoryParams) -> None:
    h = world.get(p.hero)
    m = world.get(p.helper)
    y = world.get("yacht")
    s = world.get("snout")

    world.say(
        f"Long ago, {h.id} and {m.id} came to {y.label}, a little yacht that waited by the blue water."
        f" On its bow sat {s.label}, a small snout charm that shone with {p.magic_kind}."
    )
    world.say(
        f"The children loved the yacht because it could sing softly when the breeze touched its ropes."
        f" They believed the snout charm was lucky, and in fairy tales, lucky things often wake up when needed."
    )
    world.para()
    world.say(
        f"Then {p.trouble} rolled over the sea, and the yacht slowed to a hush."
        f" The mast trembled, the lantern swung, and even brave hearts felt a little wobble."
    )
    world.say(
        f"{m.id} touched the snout charm and whispered, 'Please help us.'"
        f" At once, {s.label} gave a warm little glow, and {h.id} felt courage bloom like a candle in winter."
    )
    _apply_magic(world)
    world.para()
    world.say(
        f"The magic did not make the storm vanish."
        f" Instead, it brightened the yacht's way, and the helm turned true toward the safe shore."
    )
    world.say(
        f"{h.id} and {m.id} worked together, one at the rope and one at the lantern, while {y.label} rocked but did not break."
    )
    world.para()
    world.say(
        f"By dusk, the yacht had {p.ending}, and the snout charm still glimmered at the bow."
        f" The children laughed, not because the sea was small, but because they had learned how to keep going when it was large."
    )

    world.facts["outcome"] = "safe"
    world.facts["magic_used"] = True


def generate(params: StoryParams) -> StorySample:
    world = World()
    _setup(world, params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a fairy tale about {p.hero} and {p.helper} on a yacht with a magical snout charm.",
        f"Tell a child-friendly story where a yacht is helped by magic when {p.trouble} appears.",
        f"Make a small sea adventure with a yacht, a snout charm, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    y = world.facts["yacht"]
    s = world.facts["snout"]
    h = world.facts["helper"]
    return [
        QAItem(
            question=f"What was special about the yacht in the story?",
            answer=f"The yacht was magical, and it carried {y.label} by the blue water.",
        ),
        QAItem(
            question=f"What did the snout charm do?",
            answer=f"The snout charm gave off a warm glow and helped the children feel brave.",
        ),
        QAItem(
            question=f"What happened when {p.trouble} came?",
            answer=f"The yacht slowed down, but the magic lit the way and the children steered toward shore.",
        ),
        QAItem(
            question=f"Who helped {p.hero} on the yacht?",
            answer=f"{h.id} helped by whispering to the snout charm and working together on deck.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the yacht {p.ending}, and the snout charm still shining at the bow.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a yacht?",
            answer="A yacht is a boat that can sail on water, often for a pleasant journey.",
        ),
        QAItem(
            question="What is a snout?",
            answer="A snout is the nose or nose-like front part of an animal, and in fairy tales it can also be a lucky charm shape.",
        ),
        QAItem(
            question="What does magic do in fairy tales?",
            answer="Magic can help characters in special ways, like giving light, courage, or a surprising way forward.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.magic:
            bits.append("magic")
        if e.can_sail:
            bits.append("can_sail")
        if e.has_snout:
            bits.append("has_snout")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"{e.id}: " + ", ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
magic_used :- yacht(Y), snout(S), glow(S,1), motion(Y,1).
safe_end :- magic_used.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("yacht", "yacht"),
        asp.fact("snout", "snout"),
        asp.fact("glow", "snout", 1),
        asp.fact("motion", "yacht", 1),
    ])


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show magic_used/0.\n#show safe_end/0."))
    atoms = {sym.name for sym in model}
    ok = atoms == {"magic_used", "safe_end"}
    print("OK: ASP parity" if ok else f"MISMATCH: {atoms}")
    return 0 if ok else 1


def asp_summary() -> str:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show magic_used/0.\n#show safe_end/0."))
    return ", ".join(sorted(sym.name for sym in model))


def resolve_validity(args: argparse.Namespace) -> None:
    if args.hero and args.helper and args.hero == args.helper:
        raise StoryError("The hero and helper must be different children.")
    if args.ship_name is not None and not args.ship_name.strip():
        raise StoryError("The yacht needs a name.")
    if args.charm_name is not None and not args.charm_name.strip():
        raise StoryError("The snout charm needs a name.")


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
        print(asp_program("#show magic_used/0.\n#show safe_end/0.", ""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_summary())
        return

    if args.all:
        params_list = [
            StoryParams(hero="Anya", hero_type="girl", helper="Milo", helper_type="boy",
                        ship_name="Pearl Yacht", charm_name="snout charm",
                        magic_kind="moon magic", trouble="a fog wall", ending="sailed safely home"),
            StoryParams(hero="Cleo", hero_type="girl", helper="Rosie", helper_type="girl",
                        ship_name="Star Yacht", charm_name="golden snout",
                        magic_kind="gentle magic", trouble="a sleepy wind", ending="glided into harbor"),
            StoryParams(hero="Bram", hero_type="boy", helper="Pip", helper_type="boy",
                        ship_name="Little Yacht", charm_name="snout shell",
                        magic_kind="tide magic", trouble="a tangled rope", ending="found the bright shore"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        rng = random.Random(base)
        resolve_validity(args)
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            samples.append(generate(params))

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
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
