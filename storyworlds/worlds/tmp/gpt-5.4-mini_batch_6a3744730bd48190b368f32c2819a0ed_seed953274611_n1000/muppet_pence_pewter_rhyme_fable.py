#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/muppet_pence_pewter_rhyme_fable.py
====================================================================

A small fable-like storyworld with rhyme, centered on a muppet, a few pence,
and a pewter prize. The domain is intentionally tiny: a child and their puppet
friend visit a market stall, spend honest pence, and learn that a kind fix is
better than a sneaky swap.

The world model tracks physical state with meters and feelings with memes.
The story changes based on simulated state, not by swapping nouns in one frozen
template. The prose is written to feel like a short rhyming fable.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"gleam": 0.0, "wobble": 0.0, "mended": 0.0, "spent": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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
        import copy

        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    market: str = "fair"
    child_name: str = "Nell"
    child_type: str = "girl"
    muppet_name: str = "Mop"
    stallkeeper: str = "the seller"
    rhyme_mode: str = "couplets"
    twist: str = "honesty"
    seed: Optional[int] = None


MARKETS = {
    "fair": {"scene": "the village fair", "stall": "a bright stall"},
    "bazaar": {"scene": "the busy bazaar", "stall": "a little table of wares"},
    "green": {"scene": "the green", "stall": "a cloth-draped cart"},
}

RHYME_ENDINGS = {
    "couplets": ("light", "bright"),
    "lilt": ("day", "way"),
}

MUPPETS = ["Mop", "Nib", "Pip", "Tess"]
CHILD_NAMES = ["Nell", "Ada", "Pru", "Finn", "Bea", "Oli"]


def valid_combos() -> list[tuple[str, str]]:
    return [(m, r) for m in MARKETS for r in RHYME_ENDINGS]


ASP_RULES = r"""
valid(Market, Rhyme) :- market(Market), rhyme(Rhyme).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for m in MARKETS:
        lines.append(asp.fact("market", m))
    for r in RHYME_ENDINGS:
        lines.append(asp.fact("rhyme", r))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only python:", sorted(py - cl))
        print("  only clingo:", sorted(cl - py))

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test story generation works.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming fable about a muppet and pewter pence.")
    ap.add_argument("--market", choices=MARKETS)
    ap.add_argument("--name")
    ap.add_argument("--muppet")
    ap.add_argument("--rhyme", choices=RHYME_ENDINGS)
    ap.add_argument("--twist", choices=["honesty", "repair"])
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
    combo_ok = valid_combos()
    market = args.market or rng.choice([m for m, _ in combo_ok])
    rhyme = args.rhyme or rng.choice([r for _, r in combo_ok])
    if (market, rhyme) not in combo_ok:
        raise StoryError("That market and rhyme mode do not fit this tiny world.")

    name = args.name or rng.choice(CHILD_NAMES)
    muppet = args.muppet or rng.choice(MUPPETS)
    twist = args.twist or rng.choice(["honesty", "repair"])
    return StoryParams(market=market, child_name=name, child_type="girl", muppet_name=muppet, stallkeeper="the seller", rhyme_mode=rhyme, twist=twist)


def _moral_line() -> str:
    return "A honest little choice can shine like gold."


def generate(params: StoryParams) -> StorySample:
    if params.market not in MARKETS:
        raise StoryError(f"Unknown market: {params.market}")
    if params.rhyme_mode not in RHYME_ENDINGS:
        raise StoryError(f"Unknown rhyme mode: {params.rhyme_mode}")

    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    muppet = world.add(Entity(id=params.muppet_name, kind="character", type="muppet", role="helper"))
    seller = world.add(Entity(id="Seller", kind="character", type="adult", label=params.stallkeeper, role="adult"))
    pewter_cup = world.add(Entity(id="cup", kind="thing", type="pewter", label="pewter cup", role="prize"))
    pence = world.add(Entity(id="pence", kind="thing", type="coin", label="three pence", role="payment"))

    child.memes["joy"] += 1
    muppet.memes["joy"] += 1
    pewter_cup.meters["gleam"] = 1.0

    scene = MARKETS[params.market]["scene"]
    stall = MARKETS[params.market]["stall"]
    end_a, end_b = RHYME_ENDINGS[params.rhyme_mode]

    world.say(
        f"At {scene}, by {stall}, {child.id} and {muppet.id} went with a hop and a twirl, "
        f"for every small fable should start with a girl."
    )
    world.say(
        f'"A pewter cup!" cried {child.id}. "It shines like a star in the air." '
        f'"Three pence will do," said {seller.label}, "if you pay with care."'
    )

    world.para()
    world.say(
        f"{child.id} counted the {pence.label} and felt a small thrill. "
        f"{muppet.id} bobbed beside {child.id}, as puppets so often will."
    )

    if params.twist == "honesty":
        child.memes["worry"] += 1
        world.say(
            f"But the cup tipped a little, and gave a small clink on the tray. "
            f"{child.id} hid {child.id.lower() if False else 'the thought'}? No -- {muppet.id} said, "
            f'"Tell the truth now, and keep the day straight away."'
        )
        world.say(
            f"{child.id} owned up at once, and {seller.label} only smiled. "
            f'"A careful heart is better than tricks," {seller.label} said mild.'
        )
        pewter_cup.meters["mended"] = 1.0
        pence.meters["spent"] = 3.0
        child.memes["pride"] += 1
        muppet.memes["pride"] += 1
        child.memes["lesson"] += 1
        muppet.memes["lesson"] += 1
        world.para()
        world.say(
            f"So {child.id} paid the {pence.label}, and the cup stayed fine. "
            f"{muppet.id} grinned, and the fair felt merry and kind."
        )
        world.say(
            f"Their little fable ended in {end_a} and {end_b}, "
            f"with honesty shining like butter on bread."
        )
    else:
        world.say(
            f"The cup had a tiny wobble, but {child.id} wiped it clean. "
            f"{muppet.id} helped with a cloth, and the stall grew serene."
        )
        pewter_cup.meters["mended"] = 1.0
        pence.meters["spent"] = 3.0
        child.memes["pride"] += 1
        muppet.memes["pride"] += 1
        child.memes["lesson"] += 1
        muppet.memes["lesson"] += 1
        world.para()
        world.say(
            f"At last they paid the {pence.label} and carried the cup home. "
            f"It gleamed in the dusk like a moon made of chrome."
        )
        world.say(f"And that was the end, in {end_a} and {end_b}, of the fair little tale.")
    world.facts.update(
        child=child,
        muppet=muppet,
        seller=seller,
        cup=pewter_cup,
        pence=pence,
        market=params.market,
        rhyme_mode=params.rhyme_mode,
        twist=params.twist,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a rhyming fable for a young child that includes the words muppet, pence, and pewter at {f['market']}.",
        f"Tell a short moral story where {f['child'].id} and {f['muppet'].id} visit a stall and learn a gentle lesson about pence and a pewter cup.",
        "Write a child-friendly fable in rhyme about honesty, a market, and a shiny pewter thing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    muppet = f["muppet"]
    cup = f["cup"]
    pence = f["pence"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {muppet.id}, who visit the market together. The little fable follows what they do with the pewter cup and the pence."),
        ("What did they want to buy?", f'They wanted the pewter cup. It was the shiny prize at the stall, and it cost three pence.'),
        ("What did the muppet help with?", f"{muppet.id} helped keep the choice honest and steady. That mattered because a small problem with the cup needed a truthful fix, not a sneaky one."),
        ("How did the story end?", f"They paid the pence, kept the cup safe, and learned a moral lesson. The ending is calm and bright, which fits the fable style."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is pence?", "Pence are small coins used as money. People can count pence to pay for little things."),
        ("What is pewter?", "Pewter is a soft gray metal. It can be shaped into cups, plates, and little treasures."),
        ("What is a muppet?", "A muppet is a puppet-like character made for playful stories and shows. In this world, the muppet is a lively helper."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(market="fair", child_name="Nell", child_type="girl", muppet_name="Mop", stallkeeper="the seller", rhyme_mode="couplets", twist="honesty"),
    StoryParams(market="bazaar", child_name="Ada", child_type="girl", muppet_name="Nib", stallkeeper="the seller", rhyme_mode="lilt", twist="repair"),
    StoryParams(market="green", child_name="Pru", child_type="girl", muppet_name="Pip", stallkeeper="the seller", rhyme_mode="couplets", twist="honesty"),
]


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (market, rhyme) combos:")
        for m, r in asp_valid_combos():
            print(f"  {m:8} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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


def generation_prompts(world: World) -> list[str]:
    return generation_prompts(world)


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return world_knowledge_qa(world)


def story_qa(world: World) -> list[tuple[str, str]]:
    return story_qa(world)


if __name__ == "__main__":
    main()
