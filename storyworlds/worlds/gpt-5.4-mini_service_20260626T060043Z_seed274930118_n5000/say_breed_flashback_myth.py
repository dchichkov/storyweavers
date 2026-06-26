#!/usr/bin/env python3
"""
storyworlds/worlds/say_breed_flashback_myth.py
===============================================

A small mythic story world about speaking a true name, remembering an old vow,
and choosing which sacred beasts may breed.

Seed tale:
---
Long ago, the hill temple kept two noble beasts: a silver doe and a horned
stag. The temple child was told never to say the breeding word aloud, because it
was tied to a sleeping old god. But when the moon-shelf cracked and the beasts
grew restless, the child remembered a flashback: the high priest had once said
that only a spoken blessing could wake the right pair to breed.

The child spoke the blessing, the beasts calmed, and the old god's sign returned
to the hill.
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
    paired_with: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Shrine:
    name: str = "the hill temple"
    place: str = "the hill temple"
    sacred: bool = True


@dataclass
class Beast:
    id: str
    label: str
    phrase: str
    type: str
    sex: str
    can_breed_with: set[str]
    produces: str


@dataclass
class StoryParams:
    shrine: str
    child_name: str
    child_type: str
    guide_name: str
    guide_type: str
    beast_a: str
    beast_b: str
    seed: Optional[int] = None


class World:
    def __init__(self, shrine: Shrine) -> None:
        self.shrine = shrine
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        w = World(self.shrine)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_breed(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.entities.values() if e.kind == "character"), None)
    if child is None:
        return out
    for a in world.entities.values():
        if a.kind != "beast" or a.meters.get("restless", 0) < THRESHOLD:
            continue
        b_id = a.paired_with
        if not b_id or b_id not in world.entities:
            continue
        b = world.entities[b_id]
        if b.kind != "beast":
            continue
        sig = ("breed", a.id, b.id)
        if sig in world.fired:
            continue
        if b.meters.get("restless", 0) < THRESHOLD:
            continue
        world.fired.add(sig)
        child.meters["sign"] = 1.0
        out.append("The sacred pair accepted the blessing and the sign came back.")
    return out


CAUSAL_RULES = [_r_breed]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def beast_catalog() -> dict[str, Beast]:
    return {
        "silver_doe": Beast(
            id="silver_doe",
            label="silver doe",
            phrase="a silver doe with moon-bright eyes",
            type="doe",
            sex="female",
            can_breed_with={"horned_stag"},
            produces="fawn",
        ),
        "horned_stag": Beast(
            id="horned_stag",
            label="horned stag",
            phrase="a horned stag with ash-dark antlers",
            type="stag",
            sex="male",
            can_breed_with={"silver_doe"},
            produces="fawn",
        ),
        "river_foal": Beast(
            id="river_foal",
            label="river foal",
            phrase="a small river foal",
            type="foal",
            sex="young",
            can_breed_with=set(),
            produces="none",
        ),
    }


BEASTS = beast_catalog()
SHRINES = {"hill": Shrine()}
CHILDREN = [("Ari", "boy"), ("Mira", "girl"), ("Niko", "boy"), ("Sera", "girl")]
GUIDES = [("High Priest", "priest"), ("Old Priestess", "priestess"), ("Keeper", "priest")]
TRAITS = ["quiet", "curious", "brave", "gentle", "steadfast"]


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for a in BEASTS.values():
        for b in BEASTS.values():
            if b.id in a.can_breed_with and a.id in b.can_breed_with:
                out.append((a.id, b.id))
    return sorted(set(tuple(sorted(p)) for p in out))


def choose_pair(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    pairs = valid_pairs()
    if args.beast_a and args.beast_b:
        pair = tuple(sorted((args.beast_a, args.beast_b)))
        if pair not in pairs:
            raise StoryError("Those beasts cannot breed together in this mythic world.")
        return pair
    if args.beast_a or args.beast_b:
        fixed = args.beast_a or args.beast_b
        candidates = [p for p in pairs if fixed in p]
        if not candidates:
            raise StoryError("No compatible breeding partner exists for that beast.")
        return rng.choice(candidates)
    return rng.choice(pairs)


def build_world(params: StoryParams) -> World:
    world = World(SHRINES[params.shrine])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    guide = world.add(Entity(id=params.guide_name, kind="character", type=params.guide_type, label=params.guide_name))
    a = BEASTS[params.beast_a]
    b = BEASTS[params.beast_b]
    ea = world.add(Entity(id=a.id, kind="beast", type=a.type, label=a.label, phrase=a.phrase))
    eb = world.add(Entity(id=b.id, kind="beast", type=b.type, label=b.label, phrase=b.phrase))
    ea.paired_with = eb.id
    eb.paired_with = ea.id
    ea.owner = world.shrine.name
    eb.owner = world.shrine.name
    ea.meters["restless"] = 1.0
    eb.meters["restless"] = 1.0
    child.memes["fear"] = 1.0
    child.memes["wonder"] = 1.0
    guide.memes["memory"] = 1.0
    return world


def tell(world: World, params: StoryParams) -> None:
    child = world.get(params.child_name)
    guide = world.get(params.guide_name)
    a = world.get(params.beast_a)
    b = world.get(params.beast_b)

    world.say(f"At {world.shrine.place}, {child.name_word()} kept watch over {a.label} and {b.label}.")
    world.say(f"{child.name_word()} loved their quiet faces, but the elders said never to say the breed-word aloud.")

    world.para()
    world.say(f"One night, the moon hung low and the stones in the roof began to hum.")
    world.say(f"{a.label.capitalize()} stamped and {b.label.capitalize()} breathed hard, as if they had forgotten the old peace.")

    world.para()
    world.say(f"{child.name_word()} opened {child.pronoun('possessive')} mouth to call for help, then stopped.")
    world.say(f"That was when a flashback rose in {child.pronoun('possessive')} mind: {guide.name_word()} had once said, "
              f"\"If the sacred pair grow wild, say the blessing, and let them breed only under witness.\"")
    child.memes["memory"] = 1.0
    child.memes["resolve"] = 1.0

    world.para()
    world.say(f"So {child.name_word()} stood straight and said the blessing out loud.")
    world.say(f"{guide.name_word()} answered at once, placing a hand on each beast and nodding toward the old law.")
    a.meters["restless"] = 0.0
    b.meters["restless"] = 0.0
    propagate(world, narrate=False)
    world.say(f"The two beasts settled side by side, and the old power between them turned gentle instead of wild.")

    world.para()
    world.say(f"By dawn, a bright sign gleamed above the shrine, and {child.name_word()} knew the right pair had been honored.")
    world.say(f"The hill was quiet again, but now it felt like a place that remembered its own name.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    a = f["a"]
    b = f["b"]
    return [
        QAItem(
            question=f"Who remembered the old blessing when the two beasts became restless?",
            answer=f"{child.name_word()} remembered it after a flashback of {guide.name_word()} telling the child what to say.",
        ),
        QAItem(
            question=f"What did {child.name_word()} say to calm {a.label} and {b.label}?",
            answer="The child said the blessing out loud, and that let the sacred pair settle down.",
        ),
        QAItem(
            question=f"What changed after the blessing was spoken?",
            answer=f"The beasts became calm, the right pair could breed under witness, and a bright sign returned over the shrine.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that remembers something from earlier, so the story can explain why a character knows or feels something now.",
        ),
        QAItem(
            question="What does it mean for animals to breed?",
            answer="When animals breed, they make babies. In stories, people may speak carefully about breeding when they are watching over animals.",
        ),
        QAItem(
            question="What is a shrine?",
            answer="A shrine is a special place where people honor something holy, old, or important.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short myth about {f['child'].name_word()} who must say a blessing to calm {f['a'].label} and {f['b'].label}.",
        f"Tell a child-friendly legend with a flashback, a sacred pair, and a gentle ending at {world.shrine.place}.",
        f"Write a simple myth where someone remembers an old warning and chooses the right words when beasts need to breed.",
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
        if e.paired_with:
            bits.append(f"paired_with={e.paired_with}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A breeding pair is valid when each beast can breed with the other.
pair(A,B) :- beast(A), beast(B), can_breed(A,B), can_breed(B,A), A < B.
valid_story(C,A,B) :- child(C), pair(A,B), shrine_ok.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("shrine_ok")]
    for cid, _ in CHILDREN:
        lines.append(asp.fact("child", cid))
    for gid, _ in GUIDES:
        lines.append(asp.fact("guide", gid))
    for bid, beast in BEASTS.items():
        lines.append(asp.fact("beast", bid))
        for mate in sorted(beast.can_breed_with):
            lines.append(asp.fact("can_breed", bid, mate))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show pair/2."))
    return sorted(set(asp.atoms(model, "pair")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and valid_pairs():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about saying a blessing, a flashback, and breeding sacred beasts.")
    ap.add_argument("--shrine", choices=SHRINES, default="hill")
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-type", choices=["priest", "priestess"])
    ap.add_argument("--beast-a", choices=BEASTS)
    ap.add_argument("--beast-b", choices=BEASTS)
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
    a, b = choose_pair(args, rng)
    child_name, child_type = (args.child_name, args.child_type) if args.child_name and args.child_type else rng.choice(CHILDREN)
    guide_name, guide_type = (args.guide_name, args.guide_type) if args.guide_name and args.guide_type else rng.choice(GUIDES)
    return StoryParams(
        shrine=args.shrine,
        child_name=child_name,
        child_type=child_type,
        guide_name=guide_name,
        guide_type=guide_type,
        beast_a=a,
        beast_b=b,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
    world.facts = {
        "child": world.get(params.child_name),
        "guide": world.get(params.guide_name),
        "a": world.get(params.beast_a),
        "b": world.get(params.beast_b),
    }
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
    StoryParams("hill", "Ari", "boy", "High Priest", "priest", "silver_doe", "horned_stag"),
    StoryParams("hill", "Mira", "girl", "Old Priestess", "priestess", "horned_stag", "silver_doe"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show pair/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show pair/2."))
        pairs = sorted(set(asp.atoms(model, "pair")))
        print(f"{len(pairs)} compatible pairs:\n")
        for a, b in pairs:
            print(f"  {a} + {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
