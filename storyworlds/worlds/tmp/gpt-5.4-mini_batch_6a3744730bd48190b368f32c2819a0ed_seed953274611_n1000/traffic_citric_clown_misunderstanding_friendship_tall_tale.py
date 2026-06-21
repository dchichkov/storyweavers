#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/traffic_citric_clown_misunderstanding_friendship_tall_tale.py
==============================================================================================

A small standalone storyworld in a tall-tale register.

Premise:
- A child and a clown friend try to deliver a crate of citric fruit through
  traffic.
- A misunderstanding makes the clown think the child is angry.
- Friendship resolves the mix-up, and the delivery becomes a joyful parade.

The world uses typed entities with physical meters and emotional memes, a small
forward-chained causal model, a reasonableness gate, and an inline ASP twin.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRIDGE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    clown_name: str
    clown_gender: str
    child_trait: str
    clown_trait: str
    fruit: str
    crate: str
    traffic: str
    noise: str
    misunderstanding: str
    bridge: str = "stone bridge"
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    traffic: str
    noise: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Fruit:
    id: str
    label: str
    phrase: str
    tart: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    trigger: str
    mixup: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    if world.get("car").meters["traffic"] < THRESHOLD:
        return out
    if ("bump",) in world.fired:
        return out
    world.fired.add(("bump",))
    world.get("child").memes["worry"] += 1
    world.get("clown").memes["alarm"] += 1
    out.append("__traffic__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.get("crate").meters["shaken"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("crate").meters["open"] += 1
    out.append("__spill__")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["hurt"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["relief"] += 1
    world.get("clown").memes["relief"] += 1
    out.append("__friendship__")
    return out


CAUSAL_RULES = [Rule("bump", _r_bump), Rule("spill", _r_spill), Rule("friendship", _r_friendship)]


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


def reasonableness_gate(setting: Setting, fruit: Fruit, misunderstanding: Misunderstanding) -> bool:
    return ("traffic" in setting.afford) and ("citric" in fruit.tags) and ("misunderstanding" in misunderstanding.tags)


def bridge_ok(place: str) -> bool:
    return place in SETTINGS and "traffic" in SETTINGS[place].afford


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("car").meters["traffic"] += 1
    propagate(sim, narrate=False)
    sim.get("crate").meters["shaken"] += 1
    propagate(sim, narrate=False)
    return {
        "traffic": sim.get("car").meters["traffic"],
        "open": sim.get("crate").meters["open"],
        "worry": sim.get("child").memes["worry"],
    }


def meet(world: World, child: Entity, clown: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    clown.memes["joy"] += 1
    world.say(
        f"On a windy day in {setting.place}, {child.id} and {clown.id} set out like two bright sparks. "
        f"They meant to carry a crate of {world.facts['fruit'].label} through the {setting.traffic} at the edge of town."
    )


def load_crate(world: World, child: Entity, fruit: Fruit) -> None:
    world.say(
        f"The crate was filled with {fruit.phrase}, round and {fruit.tart}, enough to make the whole road smell sunny."
    )


def enter_traffic(world: World, clown: Entity, setting: Setting) -> None:
    world.say(
        f"But the {setting.traffic} grew thick as molasses. Horns went honk-honk, carts squeaked, and the street noise rose like a brass band."
    )
    world.get("car").meters["traffic"] += 1
    propagate(world, narrate=False)


def misunderstanding_beat(world: World, child: Entity, clown: Entity, m: Misunderstanding) -> None:
    child.memes["frustration"] += 1
    clown.memes["worry"] += 1
    world.say(
        f'Then the trouble started with a small misunderstanding. {clown.id} heard {m.trigger} and thought {m.mixup}.'
    )
    world.say(
        f'"{m.reveal}" {child.id} cried, and the clown blinked so hard that his red nose seemed to wobble all by itself.'
    )


def repair(world: World, child: Entity, clown: Entity, m: Misunderstanding) -> None:
    child.memes["hurt"] += 1
    world.say(
        f"{child.id} took a breath, spoke plain, and told the truth. {m.reveal} was what really mattered."
    )
    world.say(
        f"{clown.id} looked at {child.id}, then bowed as low as a kite string in a storm. "
        f"After that, the mix-up blew away."
    )
    propagate(world, narrate=False)


def friendship_beat(world: World, child: Entity, clown: Entity, fruit: Fruit, bridge: str) -> None:
    child.memes["trust"] += 1
    clown.memes["trust"] += 1
    world.say(
        f"Because they were friends, they did not leave the crate by the curb. Instead they carried it together over the {bridge}, one careful step at a time."
    )
    world.say(
        f"The {fruit.label} arrived shining and safe, and the clown gave one grateful bow while {child.id} laughed so hard the river birds flew up in a blue cloud."
    )


def tall_tale_end(world: World, child: Entity, clown: Entity, fruit: Fruit) -> None:
    world.say(
        f"By sunset the whole town was sharing {fruit.phrase}, and folks said the air tasted like a festival and a lemonade dream."
    )
    world.say(
        f"{child.id} and {clown.id} rolled home as happy as lanterns, with friendship in their pockets and citric sunshine in the crate."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    fruit = FRUITS[params.fruit]
    m = MISUNDERSTANDINGS[params.misunderstanding]
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child", traits=[params.child_trait]))
    clown = world.add(Entity(id=params.clown_name, kind="character", type=params.clown_gender, role="friend", traits=[params.clown_trait]))
    world.add(Entity(id="car", kind="thing", type="vehicle", label="delivery cart"))
    world.add(Entity(id="crate", kind="thing", type="crate", label=params.crate))
    world.facts.update(fruit=fruit, misunderstanding=m, setting=setting, bridge=params.bridge)

    meet(world, child, clown, setting)
    load_crate(world, child, fruit)
    world.para()
    enter_traffic(world, clown, setting)
    misunderstanding_beat(world, child, clown, m)
    world.para()
    repair(world, child, clown, m)
    friendship_beat(world, child, clown, fruit, params.bridge)
    world.para()
    tall_tale_end(world, child, clown, fruit)
    return world


SETTINGS = {
    "fair": Setting(id="fair", place="the county fair road", traffic="traffic", noise="clatter and honks", afford={"traffic"}),
    "bridge": Setting(id="bridge", place="the old bridge road", traffic="traffic", noise="river wind and horns", afford={"traffic"}),
    "market": Setting(id="market", place="the market lane", traffic="traffic", noise="bells and carts", afford={"traffic"}),
}

FRUITS = {
    "orange": Fruit(id="orange", label="oranges", phrase="a heap of oranges", tart="citric and bright", tags={"citric"}),
    "lemon": Fruit(id="lemon", label="lemons", phrase="a basket of lemons", tart="citric and sharp", tags={"citric"}),
    "lime": Fruit(id="lime", label="limes", phrase="a crate of limes", tart="citric and lively", tags={"citric"}),
}

MISUNDERSTANDINGS = {
    "tear": Misunderstanding(id="tear", trigger="a tear on the wrapping paper", mixup="the child was angry", reveal="I was only worried about the crate", tags={"misunderstanding"}),
    "wave": Misunderstanding(id="wave", trigger="a big wave of the hand", mixup="the clown was scolding", reveal="I was only waving the traffic aside", tags={"misunderstanding"}),
    "frown": Misunderstanding(id="frown", trigger="a serious frown", mixup="the child wanted to quit", reveal="I was only thinking hard about the route", tags={"misunderstanding"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for f in FRUITS:
            for m in MISUNDERSTANDINGS:
                if reasonableness_gate(SETTINGS[p], FRUITS[f], MISUNDERSTANDINGS[m]):
                    combos.append((p, f, m))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    fruit, m, setting = f["fruit"], f["misunderstanding"], f["setting"]
    return [
        f'Write a tall-tale story for a child that uses the words "traffic", "{fruit.label}", and "clown".',
        f"Tell a friendship story where a clown and a child get tangled in {setting.traffic} and a misunderstanding, then fix it with kindness.",
        f"Write a big-hearted story in a tall-tale style where citric fruit is carried through traffic and a misunderstanding is cleared up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fruit, m, setting = f["fruit"], f["misunderstanding"], f["setting"]
    return [
        QAItem(
            question="What were the friends carrying?",
            answer=f"They were carrying {fruit.phrase}. It was citric and bright, and they wanted to get it safely across the traffic.",
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"The misunderstanding began when {m.trigger}. That made the other friend think someone was upset, even though the real meaning was kinder.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They stopped, explained themselves, and listened to each other. Friendship helped them cross the {setting.traffic} together instead of arguing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does citric mean?",
            answer="Citric means tasting like citrus fruit such as lemons, limes, and oranges. Those fruits are often bright, sour, and sunny-tasting.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about what another person meant. Once they talk it through, the mistake can clear up.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means caring about someone and helping each other. Friends listen, forgive, and try again when a moment goes wrong.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n,) in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="fair",
        child_name="Mina",
        child_gender="girl",
        clown_name="Bobo",
        clown_gender="boy",
        child_trait="brave",
        clown_trait="silly",
        fruit="orange",
        crate="a painted crate",
        traffic="traffic",
        noise="clatter and honks",
        misunderstanding="tear",
        bridge="old bridge",
        seed=1,
    ),
    StoryParams(
        place="market",
        child_name="Eli",
        child_gender="boy",
        clown_name="Pippa",
        clown_gender="girl",
        child_trait="thoughtful",
        clown_trait="kind",
        fruit="lime",
        crate="a bright crate",
        traffic="traffic",
        noise="bells and carts",
        misunderstanding="wave",
        bridge="stone bridge",
        seed=2,
    ),
    StoryParams(
        place="bridge",
        child_name="Nora",
        child_gender="girl",
        clown_name="Toby",
        clown_gender="boy",
        child_trait="curious",
        clown_trait="gentle",
        fruit="lemon",
        crate="a sturdy crate",
        traffic="traffic",
        noise="river wind and horns",
        misunderstanding="frown",
        bridge="old bridge",
        seed=3,
    ),
]


def explain_rejection() -> str:
    return "(No story: this combination does not make a believable traffic-and-friendship misunderstanding.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Traffic, citric fruit, clown, misunderstanding, and friendship in a tall-tale world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--fruit", choices=FRUITS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--clown-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.place is None or c[0] == args.place)
              and (args.fruit is None or c[1] == args.fruit)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError(explain_rejection())
    place, fruit, misunderstanding = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    clown_gender = "boy" if child_gender == "girl" else "girl"
    return StoryParams(
        place=place,
        child_name=args.child_name or rng.choice(["Mina", "Nora", "Eli", "Jo", "Tess", "Bram"]),
        child_gender=child_gender,
        clown_name=args.clown_name or rng.choice(["Bobo", "Pippa", "Toby", "Momo", "Lala", "Zig"]),
        clown_gender=clown_gender,
        child_trait=rng.choice(["brave", "thoughtful", "curious", "kind"]),
        clown_trait=rng.choice(["silly", "gentle", "kind", "patient"]),
        fruit=fruit,
        crate=rng.choice(["a painted crate", "a bright crate", "a sturdy crate"]),
        traffic="traffic",
        noise=SETTINGS[place].noise,
        misunderstanding=misunderstanding,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.fruit not in FRUITS:
        raise StoryError("Unknown fruit.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if not reasonableness_gate(SETTINGS[params.place], FRUITS[params.fruit], MISUNDERSTANDINGS[params.misunderstanding]):
        raise StoryError(explain_rejection())
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


ASP_RULES = r"""
valid(P,F,M) :- setting(P), fruit(F), misunderstanding(M), citric(F), has_traffic(P), misunderstanding_tag(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("has_traffic", sid))
    for fid, fruit in FRUITS.items():
        lines.append(asp.fact("fruit", fid))
        if "citric" in fruit.tags:
            lines.append(asp.fact("citric", fid))
    for mid, mm in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding_tag", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import per contract
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combo sets differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"MISMATCH: generation smoke test failed: {e}")
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print("  ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
