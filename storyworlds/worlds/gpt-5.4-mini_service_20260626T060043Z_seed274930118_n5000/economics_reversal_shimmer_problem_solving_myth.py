#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/economics_reversal_shimmer_problem_solving_myth.py
=========================================================================================================================

A small mythic story world about economics, reversal, shimmer, and problem solving.

Seed tale premise:
A village keeps its harvest in a bright market hall. A careful child notices that
the glittering coin-chest is not growing, even though the people keep trading.
When the old exchange rule starts helping the wrong people, the child and the
keeper must reverse the rule, solve the shortage, and restore a fair flow of
goods.

The world is built around:
- a market where goods and services are exchanged,
- a reversible rule that once helped but later causes a problem,
- a shimmer-sign that reveals what is really happening,
- and a myth-style resolution where wisdom, not force, repairs the balance.

The generated stories are classical, short mythic scenes with:
premise -> tension -> turn -> resolution.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the market hall"
    place_kind: str = "market"
    gleam: str = "a silver shimmer"
    afford: set[str] = field(default_factory=lambda: {"trade", "measure", "count"})


@dataclass
class Good:
    id: str
    label: str
    phrase: str
    value: int
    scarce: bool = False
    shimmer: bool = False


@dataclass
class Rule:
    name: str
    apply: callable


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.turns: int = 0

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
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.turns = self.turns
        return clone


def _r_shimmer_reveal(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.entities.get("keeper")
    chest = world.entities.get("chest")
    if not keeper or not chest:
        return out
    if keeper.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chest.meters["shimmer"] = chest.meters.get("shimmer", 0) + 1
    out.append("The chest shone with a thin shimmer, and the truth showed itself.")
    return out


def _r_reversal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reverse_done"):
        return out
    child = world.entities.get("child")
    keeper = world.entities.get("keeper")
    if not child or not keeper:
        return out
    if child.memes.get("insight", 0) < THRESHOLD:
        return out
    sig = ("reversal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["reverse_done"] = True
    world.facts["old_rule"] = "first coin to the loudest buyer"
    world.facts["new_rule"] = "one share for each household before extras"
    keeper.memes["calm"] = keeper.memes.get("calm", 0) + 1
    out.append("The old rule was reversed, and the first shares were set aside for every home.")
    return out


def _r_balance(world: World) -> list[str]:
    out: list[str] = []
    market = world.entities.get("market")
    if not market:
        return out
    if market.meters.get("fairness", 0) < THRESHOLD:
        return out
    sig = ("balance",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    market.memes["peace"] = market.memes.get("peace", 0) + 1
    out.append("The market grew quiet again, like a river after the storm.")
    return out


CAUSAL_RULES = [
    Rule("shimmer_reveal", _r_shimmer_reveal),
    Rule("reversal", _r_reversal),
    Rule("balance", _r_balance),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mythic_opening(setting: Setting, hero: Entity) -> str:
    return f"In {setting.place}, there lived a small {hero.type} named {hero.id}, who listened carefully to old stories."


def describe_goods(good: Good) -> str:
    return f"{good.phrase}"


def predict_shortage(world: World, good: Good) -> bool:
    sim = world.copy()
    market = sim.get("market")
    market.meters["shortage"] = market.meters.get("shortage", 0) + 1
    market.memes["worry"] = market.memes.get("worry", 0) + 1
    propagate(sim, narrate=False)
    return bool(sim.get("market").meters.get("shortage", 0) >= THRESHOLD)


def tell(
    setting: Setting,
    hero_name: str,
    hero_type: str,
    keeper_type: str,
    good: Good,
    reversal_name: str,
) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    keeper = world.add(Entity(id="keeper", kind="character", type=keeper_type, label="the keeper"))
    market = world.add(Entity(id="market", kind="thing", type="market", label=setting.place))
    chest = world.add(Entity(id="chest", kind="thing", type="chest", label="the coin-chest"))
    sigil = world.add(Entity(id="sigil", kind="thing", type="sign", label="the shimmer sign"))

    world.facts.update(
        hero=hero,
        keeper=keeper,
        market=market,
        chest=chest,
        sigil=sigil,
        good=good,
        reversal_name=reversal_name,
        setting=setting,
    )

    # Act 1: premise
    world.say(mythic_opening(setting, hero))
    world.say(f"{hero.id} loved the market's {setting.gleam}, and the people trusted {keeper.pronoun('possessive')} counts.")
    world.say(f"Each day, the traders brought {describe_goods(good)} to the hall and traded under the bright roof.")
    if good.scarce:
        world.say(f"But {good.label} was growing scarce, and the old exchange rule was beginning to pinch the village.")

    # Act 2: tension
    world.para()
    keeper.memes["worry"] = 1
    market.meters["shortage"] = 1
    world.say(
        f"Then {hero.id} noticed that the loudest buyers took the first coins, while quieter homes waited with empty hands."
    )
    world.say(f"{hero.id} felt a knot of concern, because a rule that once helped the strong was now hurting the small.")
    if predict_shortage(world, good):
        world.say(f"{hero.id} held still and watched the {good.label} vanish before the fair line could form.")
    propagate(world, narrate=True)

    # Act 3: problem solving and reversal
    world.para()
    hero.memes["insight"] = 1
    world.say(
        f"{hero.id} spoke to {keeper.pronoun('object')} beneath the shimmer sign and предложed a simpler order: "
        f"first one share for each household, then extras for those who still had need."
    )
    world.say(
        f"{keeper.pronoun('possessive').capitalize()} eyes softened, for the new plan did not break trade; it changed the path of trade."
    )
    market.meters["fairness"] = 1
    propagate(world, narrate=True)

    # Resolution image
    world.para()
    world.say(
        f"By dawn's end, the reversal had been made, and every table held its fair portion."
    )
    world.say(
        f"The coin-chest still shimmered, but now its light seemed kind, and {hero.id} could walk home knowing the village had enough."
    )

    return world


SETTINGS = {
    "market_hall": Setting(place="the market hall", place_kind="market", gleam="a silver shimmer", afford={"trade", "measure", "count"}),
    "river_bazaar": Setting(place="the river bazaar", place_kind="market", gleam="a gold shimmer", afford={"trade", "measure", "count"}),
    "hill_fair": Setting(place="the hill fair", place_kind="market", gleam="a bright shimmer", afford={"trade", "measure", "count"}),
}

GOODS = {
    "grain": Good(id="grain", label="grain", phrase="golden grain sacks", value=3, scarce=True, shimmer=False),
    "honey": Good(id="honey", label="honey", phrase="sticky honey jars", value=4, scarce=True, shimmer=False),
    "cloth": Good(id="cloth", label="cloth", phrase="blue cloth bundles", value=5, scarce=False, shimmer=True),
    "salt": Good(id="salt", label="salt", phrase="small salt bowls", value=2, scarce=True, shimmer=True),
}

GENDERS = ["girl", "boy"]
GIRL_NAMES = ["Asha", "Mira", "Nia", "Suri", "Lea", "Tala"]
BOY_NAMES = ["Kiran", "Arin", "Taro", "Nilo", "Eli", "Ravi"]
KEEPER_TYPES = ["merchant", "elder", "scribe", "warden"]
HERO_TRAITS = ["curious", "steady", "brave", "patient", "wise", "gentle"]


@dataclass
class StoryParams:
    place: str
    good: str
    name: str
    gender: str
    keeper_type: str
    trait: str
    reversal_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for good in GOODS:
            combos.append((place, good))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic economics reversal story world with shimmer and problem solving.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--good", choices=GOODS.keys())
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--keeper-type", choices=KEEPER_TYPES)
    ap.add_argument("--trait", choices=HERO_TRAITS)
    ap.add_argument("--reversal-name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.good:
        combos = [c for c in combos if c[1] == args.good]
    if not combos:
        raise StoryError("No valid story combination matches those choices.")
    place, good = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    keeper_type = args.keeper_type or rng.choice(KEEPER_TYPES)
    trait = args.trait or rng.choice(HERO_TRAITS)
    reversal_name = args.reversal_name or "the fair share rule"
    return StoryParams(place=place, good=good, name=name, gender=gender, keeper_type=keeper_type, trait=trait, reversal_name=reversal_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    good = f["good"]
    setting = f["setting"]
    return [
        f'Write a short myth for a child about economics, reversal, and shimmer set in {setting.place}.',
        f"Tell a problem-solving myth where {hero.id} notices a trade rule hurting the village's {good.label}.",
        f'Write a gentle legend about a shimmering market and the moment a fair rule is chosen instead of an unfair one.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    keeper = f["keeper"]
    good = f["good"]
    setting = f["setting"]
    trait = f["hero"].type
    return [
        QAItem(
            question=f"Who noticed that the old trade rule was hurting the village at {setting.place}?",
            answer=f"{hero.id} noticed it first. {hero.id} was the small {trait} who watched the market carefully."
        ),
        QAItem(
            question=f"What was scarce in the story?",
            answer=f"{good.label} was scarce, and that made the old exchange rule cause trouble for the village."
        ),
        QAItem(
            question=f"How did the keeper and {hero.id} solve the problem?",
            answer=f"They reversed the old rule and made sure each household received one share before extras were given."
        ),
        QAItem(
            question=f"What did the shimmer show?",
            answer=f"The shimmer showed the truth of the market: the chest and the trade rule were not keeping the village fair."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is economics?",
            answer="Economics is the way people make, share, buy, and trade things they need or want."
        ),
        QAItem(
            question="What is a reversal?",
            answer="A reversal is when something changes direction or changes from one rule to its opposite."
        ),
        QAItem(
            question="What is shimmer?",
            answer="Shimmer is a soft, shining light that glints and twinkles."
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means finding a smart way to fix a hard situation."
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place(p1).
place(p2).
place(p3).

good(g1).
good(g2).
good(g3).
good(g4).

economics(place_market) :- place(_).

reversal_needed(P, G) :- place(P), good(G).
fair_rule(P, G) :- reversal_needed(P, G).
problem_solved(P, G) :- fair_rule(P, G).

shimmer_seen(P) :- place(P).
valid_story(P, G) :- reversal_needed(P, G), shimmer_seen(P), problem_solved(P, G).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for gid in GOODS:
        lines.append(asp.fact("good", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = {(a, b) for (a, b) in asp_valid_combos()}
    if len(cl) == len(py):
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    good = GOODS[params.good]
    world = tell(setting, params.name, params.gender, params.keeper_type, good, params.reversal_name)
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
    StoryParams(place="market_hall", good="grain", name="Asha", gender="girl", keeper_type="elder", trait="wise", reversal_name="the fair share rule"),
    StoryParams(place="river_bazaar", good="honey", name="Kiran", gender="boy", keeper_type="merchant", trait="curious", reversal_name="the first-share law"),
    StoryParams(place="hill_fair", good="salt", name="Mira", gender="girl", keeper_type="scribe", trait="patient", reversal_name="the even-hand rule"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return

    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.good} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
