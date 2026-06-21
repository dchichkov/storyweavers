#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/formulate_papita_buy_cautionary_twist_humor_space.py
====================================================================================

A standalone storyworld for a small Space Adventure domain with a cautionary,
slightly twisty, funny snack errand.

Premise:
- Two children are on a tiny space trip.
- They want to buy papita from a moon kiosk.
- One child wants to formulate a clever plan for eating it right away.
- The other warns that loose crumbs in zero-g can drift into buttons and vents.
- A calm grown-up suggests a safe container and a tidy route.
- The ending uses a small twist: the "papita" turns out to be a crunchy space
  potato puff, and the children happily eat it without making a floating mess.

The script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- QA from world state, not from rendered English
- Python reasonableness gate plus inline ASP twin
- support for --verify, --all, --qa, --json, --trace, --asp, --show-asp

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/formulate_papita_buy_cautionary_twist_humor_space.py
    python storyworlds/worlds/gpt-5.4-mini/formulate_papita_buy_cautionary_twist_humor_space.py --all
    python storyworlds/worlds/gpt-5.4-mini/formulate_papita_buy_cautionary_twist_humor_space.py --verify
    python storyworlds/worlds/gpt-5.4-mini/formulate_papita_buy_cautionary_twist_humor_space.py -n 5 --seed 7 --qa
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    crumby: bool = False
    edible: bool = False
    sealed: bool = False
    gives_light: bool = False

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    scene: str
    route: str
    sky: str

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
class Snack:
    id: str
    label: str
    phrase: str
    twist_label: str
    crumbs: bool = True
    edible: bool = True

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
class Risk:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_crumbs(world: World) -> list[str]:
    out: list[str] = []
    station = world.entities.get("station")
    for snack in list(world.entities.values()):
        if not snack.crumby or snack.meters["opened"] < THRESHOLD:
            continue
        sig = ("crumbs", snack.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if station:
            station.meters["mess"] += 1
        for kid in world.characters():
            kid.memes["alarm"] += 1
        out.append("__crumbs__")
    return out


CAUSAL_RULES = [Rule("crumbs", "physical", _r_crumbs)]


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


def sensible_risks() -> list[Risk]:
    return [r for r in RISKS.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(snack: Snack, setting: Setting) -> bool:
    return snack.crumbs and "zero-g" in setting.route


def is_safe_container(container: Entity, snack: Snack) -> bool:
    return container.sealed and snack.crumbs


def needs_formulation(world: World, hero: Entity, snack: Snack) -> bool:
    return hero.memes["curiosity"] >= 1 and snack.edible


def predict_opening(world: World, snack_id: str) -> dict:
    sim = world.copy()
    sim.get(snack_id).meters["opened"] += 1
    propagate(sim, narrate=False)
    return {
        "mess": sim.get("station").meters["mess"],
        "alarm": sum(k.memes["alarm"] for k in sim.characters()),
    }


def buy_snack(world: World, hero: Entity, snack: Snack, vendor: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} and {vendor.id} went to buy {snack.phrase} at the moon kiosk. "
        f"The vendor winked and said, \"One papita, extra crisp, coming up.\""
    )


def formulate_plan(world: World, hero: Entity, sidekick: Entity, snack: Snack) -> None:
    hero.memes["clever"] += 1
    world.say(
        f"{hero.id} tried to formulate a plan for eating {snack.label} right away. "
        f"{sidekick.id} tilted {sidekick.pronoun('possessive')} head and looked at the tiny vents."
    )


def warn(world: World, sidekick: Entity, hero: Entity, snack: Snack, setting: Setting) -> None:
    pred = predict_opening(world, "snack")
    sidekick.memes["careful"] += 1
    world.facts["pred"] = pred
    world.say(
        f'"{hero.id}, no open snack bags in {setting.route}," {sidekick.id} said. '
        f'"If the crumbs float, they may tickle the control panel and make the rover sneeze."'
    )


def twist(world: World, vendor: Entity, snack: Snack) -> None:
    world.say(
        f"The vendor laughed. \"Twist!\" {vendor.pronoun()} said. "
        f"\"Papita is not a potato chip here -- it is a puff from the comet bakery.\""
    )


def use_container(world: World, hero: Entity, container: Entity, snack: Snack) -> None:
    container.meters["full"] += 1
    world.say(
        f"So {hero.id} tucked the {snack.label} into a sealed lunch pod and waited."
    )


def open_safely(world: World, hero: Entity, snack: Snack, container: Entity) -> None:
    snack.meters["opened"] += 1
    propagate(world)
    world.say(
        f"Inside the pod, the {snack.label} stayed neat, and not a crumb escaped."
    )


def ending(world: World, hero: Entity, sidekick: Entity, snack: Snack, setting: Setting) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"In the soft light of the station window, {hero.id} and {sidekick.id} ate the "
        f"{snack.twist_label} papita, and the whole rover stayed spotless. "
        f"They giggled because the safest snack had also been the funniest one."
    )


def tell(setting: Setting, snack: Snack, risk: Risk, name: str = "Mina",
         sidekick_name: str = "Roo", parent_name: str = "Captain") -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type="girl", role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="boy", role="sidekick"))
    parent = world.add(Entity(id=parent_name, kind="character", type="adult", role="parent", label="the captain"))
    station = world.add(Entity(id="station", type="place", label=setting.place))
    snack_ent = world.add(Entity(id="snack", type="snack", label=snack.label, crumby=snack.crumbs, edible=snack.edible))
    pod = world.add(Entity(id="pod", type="container", label="lunch pod", sealed=True))

    hero.memes["curiosity"] = 1
    sidekick.memes["careful"] = 1

    world.say(
        f"On a bright day above the blue planet, {hero.id} and {sidekick.id} drifted through "
        f"{setting.scene}. {setting.sky}."
    )
    world.say(
        f"They wanted to buy {snack.phrase} at the kiosk, because a space adventure was more fun with a snack."
    )
    world.para()
    formulate_plan(world, hero, sidekick, snack)
    warn(world, sidekick, hero, snack, setting)
    buy_snack(world, hero, snack, parent)
    twist(world, parent, snack)
    if risk.id == "safe":
        world.para()
        use_container(world, hero, pod, snack)
        open_safely(world, hero, snack, pod)
        ending(world, hero, sidekick, snack, setting)
        outcome = "safe"
    else:
        snack_ent.meters["opened"] += 1
        propagate(world)
        world.say(
            f"But the tiny crumbs slipped out anyway, and the dashboard made a squeaky beep."
        )
        world.say(
            f"{parent.label_word.capitalize()} hurried over, closed the bag, and showed them a safer way."
        )
        ending(world, hero, sidekick, snack, setting)
        outcome = "messy"
    world.facts.update(hero=hero, sidekick=sidekick, parent=parent, station=station,
                       snack=snack_ent, pod=pod, setting=setting, risk=risk,
                       outcome=outcome, snack_cfg=snack)
    return world


SETTINGS = {
    "lunar_market": Setting("lunar_market", "the moon kiosk", "the silver market corridor", "zero-g hallway", "The stars were hanging close and bright"),
    "orbital_bay": Setting("orbital_bay", "the station shop", "the glassy orbital bay", "zero-g walkway", "The planet turned slowly below the windows"),
}

SNACKS = {
    "papita": Snack("papita", "papita", "papita", "crunchy comet puff", crumbs=True, edible=True),
    "moon_bun": Snack("moon_bun", "moon bun", "moon bun", "round moon bun", crumbs=False, edible=True),
}

RISKS = {
    "safe": Risk("safe", 3, 3, "closed the bag and used the pod", "could not stop the crumbs", "used a sealed pod so the snack stayed tidy"),
    "messy": Risk("messy", 2, 1, "messed up the corridor", "could not stop the crumbs", "forgot the pod and made a floating mess"),
}

GIRL_NAMES = ["Mina", "Lia", "Nia", "Zara", "Tia"]
BOY_NAMES = ["Roo", "Kai", "Tomo", "Ben", "Pax"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for snack_id, snack in SNACKS.items():
            if hazard_at_risk(snack, setting):
                combos.append((sid, snack_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    snack: str
    risk: str
    name: str
    sidekick: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small Space Adventure story that includes the words "formulate", "papita", and "buy".',
        f'Tell a cautionary funny story where {f["hero"].id} wants to formulate a plan to buy {f["snack_cfg"].label}, but a careful friend warns about crumbs in zero-g.',
        f'Write a twisty snack story in space where papita turns out to be something unexpected and the children choose a safe container first.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick, snack, setting = f["hero"], f["sidekick"], f["snack_cfg"], f["setting"]
    return [
        (f"What did {hero.id} want to do?",
         f"{hero.id} wanted to formulate a plan to buy {snack.phrase} and eat it on the trip."),
        (f"Why did {sidekick.id} warn them?",
         f"{sidekick.id} knew crumbs could float in zero-g. The crumbs might drift into buttons and make the tiny ship messy."),
        ("What was the twist about papita?",
         f"The vendor said papita was a crunchy comet puff, not a plain chip. That made the name funny and the snack feel special."),
        ("How did the story end?",
         f"They used a sealed pod, so the snack stayed tidy and the station stayed clean. They still got to eat the papita together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does zero-g mean?",
         "Zero-g means very little gravity, so things can float instead of falling down."),
        ("Why are crumbs annoying in space?",
         "Because they can drift everywhere and get into tiny buttons, vents, or filters."),
        ("What is a sealed container for?",
         "A sealed container keeps food from spilling or floating away."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.crumby:
            bits.append("crumby")
        if e.sealed:
            bits.append("sealed")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, snack: Snack) -> str:
    if not hazard_at_risk(snack, setting):
        return "(No story: the snack would not create a zero-g crumb problem here.)"
    return "(No story: this combination is not suitable for the cautionary space-snack setup.)"


def explain_risk(rid: str) -> str:
    r = RISKS[rid]
    better = " / ".join(sorted(x.id for x in sensible_risks()))
    return f"(Refusing risk '{rid}': it is too weak for the story gate. Try: {better}.)"


def outcome_of(params: StoryParams) -> str:
    return params.risk


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure snack storyworld with caution, twist, and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if args.setting and args.snack:
        if not hazard_at_risk(SNACKS[args.snack], SETTINGS[args.setting]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], SNACKS[args.snack]))
    if args.risk and args.risk not in RISKS:
        raise StoryError(explain_risk(args.risk))
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              if args.snack is None or c[1] == args.snack]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack = rng.choice(sorted(combos))
    risk = args.risk or rng.choice(sorted(RISKS))
    name = args.name or rng.choice(GIRL_NAMES)
    sidekick = args.sidekick or rng.choice(BOY_NAMES)
    return StoryParams(setting, snack, risk, name, sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SNACKS[params.snack], RISKS[params.risk], params.name, params.sidekick)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
hazard(S, K) :- snack(S), crumby(S), zero_g(K).
valid(S, K) :- snack(S), setting(K), hazard(S, K).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("zero_g", sid))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.crumbs:
            lines.append(asp.fact("crumby", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, snack=None, risk=None, name=None, sidekick=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("lunar_market", "papita", "safe", "Mina", "Roo"),
    StoryParams("orbital_bay", "papita", "safe", "Lia", "Kai"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
