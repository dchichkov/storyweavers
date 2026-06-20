#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dapple_twist_bad_ending_humor_myth.py
=====================================================================

A small standalone story world for a myth-flavored tale about a dappled grove,
a clever twist, a funny mistake, and a bad ending that still feels child-facing
and complete.

The domain premise:
- A young helper enters a sacred grove where sunlight makes dapple patterns.
- Someone tries a boastful shortcut to gather a blessing.
- The shortcut backfires in a twist.
- Humor stays gentle and mythic.
- The ending is bad in the story sense: the prize is lost, but the people are
  safe and the world remembers the lesson.

This script follows the Storyweavers world contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
- emits registry facts with asp_facts()
- --verify checks ASP/Python parity and runs a smoke generation
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "nymph", "goddess"}
        male = {"boy", "father", "man", "god", "spryte"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Grove:
    id: str
    label: str
    dapple: str
    sacred: bool = True
    mirrored: bool = False
    can_bless: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    risky: bool = False
    weight: int = 1
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Trick:
    id: str
    label: str
    method: str
    twist: str
    fail_text: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_blush(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["shame"] < THRESHOLD:
            continue
        sig = ("blush", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["humor"] += 1
        out.append("__humor__")
    return out


def _r_loss(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("loss", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "grove" in world.entities:
            world.get("grove").meters["quiet"] += 1
        out.append("__quiet__")
    return out


CAUSAL_RULES = [Rule("blush", "social", _r_blush), Rule("loss", "physical", _r_loss)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(grove: Grove, offering: Offering, trick: Trick) -> bool:
    return grove.sacred and offering.risky and trick.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for gid, grove in GROVES.items():
        for oid, off in OFFERINGS.items():
            for tid, tr in TRICKS.items():
                if reasonableness_gate(grove, off, tr):
                    combos.append((gid, oid, tid))
    return combos


def _do_trick(world: World, offering: Entity, grove: Entity, trick: Trick, narrate: bool = True) -> None:
    offering.meters["misused"] += 1
    offering.meters["lost"] += 1
    grove.meters["disturbed"] += 1
    propagate(world, narrate=narrate)


def predict(world: World, offering_id: str, grove_id: str, trick: Trick) -> dict:
    sim = world.copy()
    _do_trick(sim, sim.get(offering_id), sim.get(grove_id), trick, narrate=False)
    return {
        "lost": sim.get(offering_id).meters["lost"] >= THRESHOLD,
        "quiet": sim.get(grove_id).meters["quiet"],
    }


def tell_opening(world: World, hero: Entity, elder: Entity, grove: Grove) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Long ago, when the {grove.label} still kept the old songs, {hero.id} "
        f"walked under {grove.dapple} with {elder.id}, who knew the path of leaves."
    )
    world.say(
        f"The light came in dappled patches, as if the sky had dropped coins of gold "
        f"between the branches."
    )


def ask_for_blessing(world: World, hero: Entity, grove: Grove, offering: Offering) -> None:
    hero.memes["desire"] += 1
    world.say(
        f'{hero.id} held up {offering.phrase} and whispered, "Great grove, give me '
        f'a sign."'
    )
    world.say(
        f'But {grove.label} only shimmered in {grove.dapple}, calm and unreadable.'
    )


def warn(world: World, elder: Entity, hero: Entity, offering: Offering, grove: Grove) -> bool:
    pred = predict(world, "offering", "grove", TRICKS["twist"])
    if not pred["lost"]:
        return False
    elder.memes["care"] += 1
    world.facts["predicted_loss"] = pred["lost"]
    world.say(
        f'{elder.id} touched {hero.pronoun("possessive")} shoulder. '
        f'"Do not gamble with a holy thing," {elder.pronoun()} said. '
        f'"That offering belongs to the altar, and the grove remembers."'
    )
    return True


def twist(world: World, hero: Entity, elder: Entity, offering: Offering, grove: Grove, trick: Trick) -> None:
    hero.memes["boldness"] += 1
    world.say(
        f'{hero.id} grinned anyway. "{trick.method.capitalize()}!" {hero.id} said, '
        f'and tried the trick {trick.twist}.'
    )
    _do_trick(world, world.get("offering"), world.get("grove"), trick)
    world.say(
        f"{trick.label.capitalize()} went wrong in a way that would have been funny "
        f"in a barnyard but not in a sacred grove."
    )


def bad_ending(world: World, hero: Entity, elder: Entity, offering: Offering, grove: Grove) -> None:
    hero.memes["regret"] += 1
    elder.memes["regret"] += 1
    world.say(
        f"Then the {offering.label} slipped away into the roots, and the sign never came."
    )
    world.say(
        f"The grove kept its own mystery, and {hero.id} had to bow and leave with "
        f"empty hands."
    )


def humor_line(world: World, hero: Entity, elder: Entity, trick: Trick) -> None:
    world.say(
        f"{elder.id} sighed, then could not help laughing a little. "
        f'"That was a royal mess," {elder.pronoun()} said, "and the roots were '
        f'not impressed."'
    )
    world.say(
        f"{hero.id} laughed too, because even a bad omen can look silly when it "
        f"spins out sideways."
    )


def lesson(world: World, hero: Entity, elder: Entity, grove: Grove) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"At sunset, {elder.id} led {hero.id} back under the branches. "
        f'"Ask for gifts with open palms, not tricks," {elder.pronoun()} said.'
    )
    world.say(
        f"{hero.id} nodded, and the dapple on the path looked gentler on the way home."
    )


def tell(grove: Grove, offering: Offering, trick: Trick, hero_name: str, hero_type: str, elder_name: str, elder_type: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_type, role="hero"))
    elder = world.add(Entity(elder_name, kind="character", type=elder_type, role="elder"))
    g = world.add(Entity("grove", type="place", label=grove.label))
    off = world.add(Entity("offering", type="thing", label=offering.label))
    world.facts["grove"] = grove
    world.facts["offering_cfg"] = offering
    world.facts["trick"] = trick

    tell_opening(world, hero, elder, grove)
    world.para()
    ask_for_blessing(world, hero, grove, offering)
    warn(world, elder, hero, offering, grove)
    world.para()
    twist(world, hero, elder, offering, grove, trick)
    bad_ending(world, hero, elder, offering, grove)
    humor_line(world, hero, elder, trick)
    world.para()
    lesson(world, hero, elder, grove)

    world.facts.update(hero=hero, elder=elder, grove_ent=g, offering_ent=off, outcome="bad")
    return world


GROVES = {
    "oak": Grove("oak", "oak grove", "dappled oak-light", sacred=True, mirrored=False, can_bless=True, tags={"dapple", "myth"}),
    "cedar": Grove("cedar", "cedar grove", "dappled cedar-light", sacred=True, mirrored=False, can_bless=True, tags={"dapple", "myth"}),
    "moonpool": Grove("moonpool", "moonpool grove", "silver dapple on black water", sacred=True, mirrored=True, can_bless=True, tags={"dapple", "myth"}),
}

OFFERINGS = {
    "bread": Offering("bread", "honey bread", "a round loaf of honey bread", risky=True, weight=1, tags={"bread"}),
    "apple": Offering("apple", "red apples", "a basket of red apples", risky=True, weight=1, tags={"fruit"}),
    "cloth": Offering("cloth", "bright cloth", "a folded bright cloth", risky=True, weight=2, tags={"cloth"}),
}

TRICKS = {
    "twist": Trick("twist", "twist", "twisting the road-sign three times", "with a wink and a hop", "it tangled the blessing instead", 3, 1, tags={"twist", "humor"}),
    "loop": Trick("loop", "loop", "looping the prayer ribbon around a branch", "backward through the shadows", "it tied the prayer into a knot", 2, 1, tags={"twist", "humor"}),
    "flip": Trick("flip", "flip", "flipping the offering over for luck", "as if upside-down made wisdom", "it sent the offering skittering away", 2, 1, tags={"twist", "humor"}),
}


@dataclass
@dataclass
class StoryParams:
    grove: str
    offering: str
    trick: str
    hero: str
    hero_type: str
    elder: str
    elder_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic dapple story with a twist, humor, and a bad ending.")
    ap.add_argument("--grove", choices=GROVES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["man", "woman"])
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
    combos = [c for c in valid_combos()
              if (args.grove is None or c[0] == args.grove)
              and (args.offering is None or c[1] == args.offering)
              and (args.trick is None or c[2] == args.trick)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    grove, offering, trick = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    elder_type = args.elder_type or rng.choice(["man", "woman"])
    hero = args.hero or rng.choice(["Ari", "Mina", "Talo", "Rhea", "Niko"])
    elder = args.elder or rng.choice(["Ila", "Orin", "Sera", "Balen"])
    return StoryParams(grove, offering, trick, hero, hero_type, elder, elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    grove = f["grove"]
    offering = f["offering_cfg"]
    trick = f["trick"]
    return [
        f'Write a myth-style story that includes the word "dapple" and ends in a bad twist.',
        f"Tell a short myth where {hero.id} brings {offering.phrase} to {grove.label} and tries a {trick.label} that goes wrong.",
        f"Write a child-facing myth with humor where a sacred grove, a risky offering, and a clever trick produce a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    grove = f["grove"]
    offering = f["offering_cfg"]
    trick = f["trick"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {elder.id}, who walked into the {grove.label}. The story follows their attempt to ask the grove for a sign."
        ),
        QAItem(
            question="What went wrong in the story?",
            answer=f"{hero.id} tried {trick.method}, but the trick failed and the offering was lost in the roots. That is the twist: the clever plan made things worse instead of better."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly because the blessing never came and {hero.id} had to leave with empty hands. Still, nobody was hurt, and the humor kept the mood gentle."
        ),
    ]
    if f["outcome"] == "bad":
        qa.append(
            QAItem(
                question=f"Why did {elder.id} laugh?",
                answer=f"{elder.id} laughed because the mistake was so awkward it looked silly after the fact. The roots tangled the trick, which made the whole moment feel like a joke from the old gods."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dappled light?",
            answer="Dappled light is sunlight that comes through leaves in little bright patches. It looks like the ground has been sprinkled with spots of gold."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a turn that surprises you. It changes what you expected to happen."
        ),
        QAItem(
            question="Why can humor help in a sad story?",
            answer="Humor can make a sad story easier to hear because it gives you a small smile. It does not fix the problem, but it softens the feeling."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for gid, g in GROVES.items():
        lines.append(asp.fact("grove", gid))
        if g.sacred:
            lines.append(asp.fact("sacred", gid))
        if g.can_bless:
            lines.append(asp.fact("can_bless", gid))
        lines.append(asp.fact("dapple", gid))
    for oid, o in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        if o.risky:
            lines.append(asp.fact("risky", oid))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        lines.append(asp.fact("power", tid, t.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(G,O,T) :- grove(G), offering(O), trick(T), sacred(G), risky(O), sense(T,S), sense_min(M), S >= M.
bad_ending(G,O,T) :- valid(G,O,T).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
        if a - p:
            print("  only in ASP:", sorted(a - p))
        if p - a:
            print("  only in Python:", sorted(p - a))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("oak", "bread", "twist", "Ari", "boy", "Ila", "woman"),
    StoryParams("cedar", "apple", "loop", "Mina", "girl", "Orin", "man"),
    StoryParams("moonpool", "cloth", "flip", "Talo", "boy", "Sera", "woman"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(GROVES[params.grove], OFFERINGS[params.offering], TRICKS[params.trick],
                 params.hero, params.hero_type, params.elder, params.elder_type)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for g, o, t in combos:
            print(f"  {g:10} {o:8} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} in the {p.grove} ({p.trick}, bad ending)"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
