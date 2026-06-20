#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/babble_nod_subway_station_reconciliation_twist_bad.py
=====================================================================================

A tiny standalone storyworld for a subway-station pirate-play tale with two
seed words ("babble", "nod"), a reconciliation beat, a twist, and a bad ending.

Premise:
- Two children turn a subway station into a pretend pirate harbor.
- One child babbles an eager plan; the other nods and follows.
- They quarrel over a lost token/map and risk missing the train.
- A twist reveals the station helper was trying to keep them safe.
- They reconcile, but the resolution comes too late: the train leaves, and the
  night ends in disappointment.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- lazy ASP helpers
- StoryParams / registries / build_parser / resolve_params / generate / emit / main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    detail: str
    noise: str

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
class ShipToy:
    id: str
    label: str
    phrase: str
    carried: str
    lost_to: str
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
class Twist:
    id: str
    clue: str
    reveal: str
    helps: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_babble_noise(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["babble"] < THRESHOLD:
            continue
        sig = ("babble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "station" in world.entities:
            world.get("station").meters["noise"] += 1
        out.append("__noise__")
    return out


def _r_lost_toy(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("lost", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            kid.memes["worry"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("babble_noise", _r_babble_noise),
    Rule("lost_toy", _r_lost_toy),
]


def hazard_possible(token: ShipToy, setting: Setting) -> bool:
    return token.lost_to == "turnstile" and "station" in setting.id


def stable_twist(twist: Twist, token: ShipToy) -> bool:
    return bool(twist.clue and token.id)


@dataclass
@dataclass
class StoryParams:
    setting: str
    token: str
    twist: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
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
    ap = argparse.ArgumentParser(
        description="A subway-station pirate-play story world with babble, nod, reconciliation, a twist, and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.token and args.setting and not hazard_possible(TOKENS[args.token], SETTINGS[args.setting]):
        raise StoryError("No story: that token does not fit the subway-station loss twist.")
    settings = [s for s in SETTINGS if args.setting in (None, s)]
    tokens = [t for t in TOKENS if args.token in (None, t)]
    twists = [t for t in TWISTS if args.twist in (None, t)]
    combos = [(s, t, w) for s in settings for t in tokens for w in twists
              if hazard_possible(TOKENS[t], SETTINGS[s]) and stable_twist(TWISTS[w], TOKENS[t])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, token, twist = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice([n for n in (BOY_NAMES if mate_gender == "boy" else GIRL_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, token, twist, hero, hero_gender, mate, mate_gender, parent)


def _do_babble(world: World, kid: Entity) -> None:
    kid.meters["babble"] += 1
    propagate(world, narrate=False)


def _do_loss(world: World, token: Entity) -> None:
    token.meters["lost"] += 1
    propagate(world, narrate=False)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(params.hero, "character", params.hero_gender, role="captain"))
    mate = world.add(Entity(params.mate, "character", params.mate_gender, role="mate"))
    parent = world.add(Entity("Parent", "character", params.parent, role="parent", label="the parent"))
    station = world.add(Entity("station", "place", "place", label=world.setting.place))
    token = world.add(Entity("token", "thing", "thing", label=TOKENS[params.token].label))
    clue = world.add(Entity("clue", "thing", "thing", label=TWISTS[params.twist].id))

    hero.memes["joy"] += 1
    mate.memes["trust"] += 1
    world.say(
        f"At {world.setting.place}, {hero.id} and {mate.id} turned the waiting area into a pirate deck. "
        f"{world.setting.detail}"
    )
    world.say(
        f'"{hero.id}, {hero.id}!" {hero.id} babbled at the echo, and {mate.id} gave a steady nod. '
        f'Their little ship game made the station feel like a harbor.'
    )

    world.para()
    world.say(
        f"But the plan needed the {token.label}, and the {token.label} had slipped near the turnstile."
    )
    world.say(f'{mate.id} bit {mate.pronoun("possessive")} lip. "{hero.id}, we should ask for help," {mate.pronoun()} said.')

    _do_babble(world, hero)
    world.say(
        f'{hero.id} babbled faster and reached for the {token.label}. Then the turnstile clicked, and the coin slipped away.'
    )
    _do_loss(world, token)
    world.say(f'{mate.id} nodded again, but this time it was not a happy nod.')

    world.para()
    world.say(
        f'Then came the twist: a station helper lifted a hand and said, "{TWISTS[params.twist].reveal}"'
    )
    world.say(TWISTS[params.twist].helps)
    hero.memes["stubborn"] += 1
    mate.memes["worry"] += 1
    world.say(
        f'{hero.id} looked at {mate.id}. {mate.id} looked back. Both children finally {params.parent} {""}'
    )
    world.say(
        f"After a small pause, they both nodded. {hero.id} said sorry first, and {mate.id} said sorry too."
    )
    hero.memes["love"] += 1
    mate.memes["love"] += 1
    hero.memes["reconcile"] += 1
    mate.memes["reconcile"] += 1
    world.say(
        f'They made up right there on the hard bench, with the station humming around them like a giant metal sea.'
    )

    world.para()
    world.say(
        f'But by then, it was too late. Their train had already left, and the shiny lights rolled away into the dark tunnel.'
    )
    world.say(
        f'{parent.label_word.capitalize()} found them on the bench and held them close, while the pirate game ended in a sad, sleepy silence.'
    )
    world.say(
        f'Their pretend harbor was still there, but the adventure was over for the night.'
    )

    world.facts.update(
        hero=hero, mate=mate, parent=parent, setting=world.setting, token=token, clue=clue,
        twist=TWISTS[params.twist], outcome="bad", reconciled=True, lost=True, station=station
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-style story for a young child set in a subway station. Include the words "babble" and "nod".',
        f"Tell a small story where {f['hero'].id} babbles too much, {f['mate'].id} nods along, they reconcile, and then a twist makes the ending sad.",
        f'Write a subway-station adventure with a pirate feel, a reconciliation scene, and a bad ending after the twist is revealed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, parent, token, twist = f["hero"], f["mate"], f["parent"], f["token"], f["twist"]
    return [
        QAItem("Who are the story about?",
               f"It is about {hero.id} and {mate.id}, two children playing pirates at the subway station. {parent.label_word.capitalize()} helps at the end when the night turns sad."),
        QAItem("What did {0} babble about?".format(hero.id),
               f"{hero.id} babbled about the pirate plan and the lost token. That noisy excitement made the station feel louder and made it harder to think clearly."),
        QAItem("Why did they reconcile?",
               f"They reconciled because they both wanted the game to be okay again after the mistake. They apologized, nodded to each other, and made up on the bench."),
        QAItem("What was the twist?",
               f"The twist was that the station helper was trying to keep them safe, not block their fun. The helper's clue showed they had misunderstood the warning."),
        QAItem("How did the story end?",
               f"It ended badly because the train had already left by the time they made up. The children were safe, but their adventure was over and they felt sad.")
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a subway station?",
               "A subway station is a place where people wait for underground trains. It usually has benches, signs, and turnstiles."),
        QAItem("What does nod mean?",
               "To nod means to move your head up and down, often to show yes or agreement. People nod when they are listening or understanding."),
        QAItem("What does babble mean?",
               "To babble means to talk quickly in a noisy, excited way. Small children often babble when they are eager or upset."),
        QAItem("Why can trains be dangerous to miss?",
               "If you miss a train, you may have to wait a long time for the next one. That can make a trip late and leave you tired or disappointed."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(out)


SETTINGS = {
    "station": Setting("station", "the subway station", "The platform smelled like old rails and rain, and a red sign blinked above the turnstile.", "hum"),
}

TOKENS = {
    "coin": ShipToy("coin", "silver token", "a silver token", "carried in a tiny pocket", "the turnstile", {"lost", "metal"}),
}

TWISTS = {
    "helper": Twist("helper", "The helper was waving them back for safety.", "We were only trying to keep you safe.", "That meant the warning was a kindness, not a trick.", {"safety", "twist"}),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("station", "coin", "helper")]


def explain_rejection(token: ShipToy, setting: Setting) -> str:
    return f"(No story: {token.label} needs the turnstile twist, and this setting won't support it.)"


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "station"), asp.fact("token", "coin"), asp.fact("twist", "helper")]
    lines.append(asp.fact("hazard", "coin", "station"))
    lines.append(asp.fact("valid", "station", "coin", "helper"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, W) :- setting(S), token(T), twist(W), hazard(T, S).
outcome(bad) :- valid(S, T, W).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: default generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams("station", "coin", "helper", "Maya", "girl", "Tom", "boy", "mother"))]
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
        header = "### subway-station pirate tale" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
