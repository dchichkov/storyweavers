#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/parliament_moral_value_animal_story.py
======================================================================

A standalone storyworld for a tiny animal tale with a parliament, a moral value,
and a concrete turn in the state of the world.

Premise:
- Animals live near a small meadow and hold a parliament in a hollow oak.
- One animal wants something tempting: a shiny shortcut, a snack, or a boast.
- Another animal worries because the choice could hurt trust, fairness, or the
  shared home.

Turn:
- The parliament debates a concrete choice driven by physical and emotional state.
- A moral value such as honesty, kindness, patience, courage, or sharing becomes
  the deciding force.

Resolution:
- The animal chooses the better action.
- The world shows the change through meters and memes: trust rises, harm falls,
  and the parliament ends with a calm, earned image.

This file follows the Storyweavers contract:
- stdlib only
- eager results import
- StoryParams, build_parser, resolve_params, generate, emit, main
- `-n`, `--all`, `--seed`, `--trace`, `--qa`, `--json`, `--asp`, `--verify`,
  `--show-asp`
- Python reasonableness gate plus inline ASP twin
- QA generated from world state, not from rendered English
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
    species: str = "animal"
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Value:
    id: str
    label: str
    action: str
    gain: str
    harm: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Offer:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Setting:
    id: str
    place: str
    meeting: str
    closing: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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


def _r_trust(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["truth"] >= THRESHOLD:
            sig = ("trust", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["trust"] += 1
            out.append("__trust__")
    return out


def _r_hurt(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["harm"] < THRESHOLD:
            continue
        sig = ("hurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__hurt__")
    return out


CAUSAL_RULES = [Rule("trust", "social", _r_trust), Rule("hurt", "social", _r_hurt)]


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


def moral_gain(value: Value) -> str:
    return value.gain


def moral_harm(value: Value) -> str:
    return value.harm


def is_reasonable(value: Value, offer: Offer, setting: Setting) -> bool:
    return value.id in {"honesty", "kindness", "sharing", "patience", "courage"} and offer.id in {"apology", "help", "share", "wait", "speak"} and setting.id == "parliament"


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (sid, vid, oid)
        for sid, s in SETTINGS.items()
        for vid, v in VALUES.items()
        for oid, o in OFFERS.items()
        if is_reasonable(v, o, s)
    ]


def forecast(world: World, hero_id: str, value_id: str, offer_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(hero_id)
    value = VALUES[value_id]
    offer = OFFERS[offer_id]
    hero.memes["temptation"] += 1
    hero.memes["moral_pull"] += 1
    hero.meters["trust"] += 1 if offer.id in {"apology", "help", "share"} else 0
    if value.id == "honesty":
        hero.memes["truth"] += 1
    if offer.id == "help":
        sim.get("bridge").meters["safe"] += 1
    return {
        "trust": sim.get(hero_id).meters["trust"],
        "harm": sim.get("bridge").meters["harm"],
    }


def setup(world: World, setting: Setting, hero: Entity, friend: Entity, elder: Entity) -> None:
    world.say(
        f"In the {setting.place}, the animal friends gathered for a small parliament "
        f"under the oak."
    )
    world.say(
        f"{hero.id}, {friend.id}, and {elder.id} sat in a circle while the leaves "
        f"shivered overhead."
    )


def temptation(world: World, hero: Entity, value: Value) -> None:
    hero.memes["temptation"] += 1
    world.say(
        f"{hero.id} wanted the quick, shiny choice, but {value.label} tugged at "
        f"{hero.pronoun('possessive')} heart."
    )


def debate(world: World, friend: Entity, hero: Entity, value: Value, setting: Setting) -> None:
    pred = forecast(world, hero.id, value.id, "help")
    friend.memes["care"] += 1
    world.facts["forecast_trust"] = pred["trust"]
    world.facts["forecast_harm"] = pred["harm"]
    world.say(
        f"{friend.id} stood and spoke softly. '{value.label.capitalize()} matters here. "
        f"If you choose wrong, the others will feel hurt, and the parliament will "
        f"remember it.'"
    )


def choose_bad(world: World, hero: Entity, value: Value) -> None:
    hero.memes["shame"] += 1
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} head, then chose the tempting "
        f"thing anyway."
    )


def choose_good(world: World, hero: Entity, value: Value, offer: Offer) -> None:
    hero.memes["truth"] += 1
    hero.memes["calm"] += 1
    world.say(
        f"{hero.id} listened, breathed in, and chose {value.action} instead of the "
        f"tempting shortcut."
    )
    world.say(f"{offer.phrase.capitalize()} made the whole circle feel safer.")


def consequence(world: World, bridge: Entity, value: Value, offer: Offer, good: bool) -> None:
    if good:
        bridge.meters["harm"] = 0.0
        bridge.meters["safe"] += 1
        bridge.meters["trust"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The choice left the bridge of trust strong, and the animals could look "
            f"one another in the eye."
        )
    else:
        bridge.meters["harm"] += 1
        bridge.memes["hurt"] += 1
        propagate(world, narrate=False)
        world.say(
            f"The wrong choice made the bridge of trust wobble, and the parliament "
            f"fell quiet."
        )


def ending(world: World, hero: Entity, friend: Entity, elder: Entity, setting: Setting, value: Value, good: bool) -> None:
    if good:
        hero.meters["trust"] += 1
        friend.meters["trust"] += 1
        elder.meters["trust"] += 1
        world.say(
            f"Before they left, the elder nodded with a smile, and the parliament "
            f"ended in warm, steady peace."
        )
        world.say(
            f"That evening, {hero.id} walked home with {value.label} shining bright "
            f"inside {hero.pronoun('possessive')} chest."
        )
    else:
        world.say(
            f"That evening, {hero.id} went home with a heavy chest, knowing the next "
            f"meeting would need a better choice."
        )


def tell(setting: Setting, value: Value, offer: Offer, hero_name: str = "Milo",
         friend_name: str = "Tessa", elder_name: str = "Auntie") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="fox", species="animal", role="speaker"))
    friend = world.add(Entity(id=friend_name, kind="character", type="rabbit", species="animal", role="listener"))
    elder = world.add(Entity(id=elder_name, kind="character", type="owl", species="animal", role="elder"))
    bridge = world.add(Entity(id="bridge", type="thing", label="the bridge"))

    hero.memes["temptation"] = 1
    friend.memes["care"] = 1
    elder.memes["wisdom"] = 2

    setup(world, setting, hero, friend, elder)
    world.para()
    temptation(world, hero, value)
    debate(world, friend, hero, value, setting)

    good = value.id in {"honesty", "kindness", "sharing", "patience", "courage"} and offer.id in {"apology", "help", "share", "wait", "speak"}
    world.para()
    if good:
        choose_good(world, hero, value, offer)
    else:
        choose_bad(world, hero, value)

    consequence(world, bridge, value, offer, good)
    world.para()
    ending(world, hero, friend, elder, setting, value, good)

    world.facts.update(
        setting=setting, value=value, offer=offer,
        hero=hero, friend=friend, elder=elder, bridge=bridge,
        outcome="good" if good else "bad",
        forecast_trust=world.facts.get("forecast_trust", 0),
        forecast_harm=world.facts.get("forecast_harm", 0),
    )
    return world


SETTINGS = {
    "parliament": Setting("parliament", "parliament hall", "the parliament", "the parliament closed"),
}

VALUES = {
    "honesty": Value("honesty", "honesty", "tell the truth", "trust grows", "secrets make hurt", {"truth"}),
    "kindness": Value("kindness", "kindness", "help kindly", "warmth grows", "roughness makes hurt", {"care"}),
    "sharing": Value("sharing", "sharing", "share fairly", "everyone feels included", "hoarding makes hurt", {"fair"}),
    "patience": Value("patience", "patience", "wait calmly", "peace grows", "rushing makes hurt", {"calm"}),
    "courage": Value("courage", "courage", "speak bravely", "brave hearts grow", "silence makes hurt", {"brave"}),
}

OFFERS = {
    "apology": Offer("apology", "an apology", "an apology softened the room", "repair"),
    "help": Offer("help", "help", "help made the work lighter", "repair"),
    "share": Offer("share", "sharing", "sharing opened the circle", "repair"),
    "wait": Offer("wait", "waiting", "waiting gave everyone time", "repair"),
    "speak": Offer("speak", "speaking up", "speaking up cleared the air", "repair"),
}

GIRL_NAMES = ["Tessa", "Mina", "Luna", "Ivy", "Nina"]
BOY_NAMES = ["Milo", "Arlo", "Otis", "Theo", "Ben"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a small child that includes the word "parliament" '
        f'and teaches a moral value about {f["value"].label}.',
        f"Tell a tiny animal parliament story where {f['hero'].id} must choose "
        f"{f['value'].label} instead of a selfish shortcut.",
        f"Write a gentle story about animals in a parliament hall that ends with a "
        f"clear moral choice and a calmer ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, elder = f["hero"], f["friend"], f["elder"]
    value, offer = f["value"], f["offer"]
    bridge = f["bridge"]
    items = [
        QAItem("Who is the story about?",
               f"It is about {hero.id}, {friend.id}, and {elder.id}, who met in the parliament and had to make a moral choice together."),
        QAItem("What choice did the main animal have to make?",
               f"{hero.id} had to choose {value.label} instead of the tempting shortcut. That choice mattered because it could either build trust or make things hurt."),
        QAItem("How did the other animal help?",
               f"{friend.id} spoke up and reminded {hero.id} about what was right. That calm warning helped the group choose the better path."),
    ]
    if f["outcome"] == "good":
        items.append(QAItem(
            "How did the story end?",
            f"It ended well because {hero.id} chose {value.action}, and the parliament felt peaceful again. The bridge of trust stayed strong, so everyone left calmer than before."
        ))
        items.append(QAItem(
            "What changed after the moral choice?",
            f"Trust grew, harm dropped away, and the animals could look at one another without shame. The better choice made the whole meeting feel safe."
        ))
    else:
        items.append(QAItem(
            "How did the story end?",
            f"It ended sadly because {hero.id} chose the wrong thing, and the parliament grew quiet. The bridge of trust wobbled, so the animals knew they would have to fix it later."
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    value = world.facts["value"]
    qa = [
        QAItem("What is a parliament?",
               "A parliament is a meeting where a group talks together and tries to make a fair choice."),
        QAItem("What is a moral value?",
               "A moral value is a good way of acting, like honesty, kindness, courage, patience, or sharing."),
    ]
    if value.id == "honesty":
        qa.append(QAItem("Why is honesty important?",
                         "Honesty helps animals trust one another, and trust makes it easier to live and work together."))
    elif value.id == "kindness":
        qa.append(QAItem("Why does kindness matter?",
                         "Kindness helps feelings heal, and gentle help makes hard days lighter for everyone."))
    elif value.id == "sharing":
        qa.append(QAItem("Why is sharing good?",
                         "Sharing helps everyone get a turn, so one animal does not keep all the good things."))
    elif value.id == "patience":
        qa.append(QAItem("Why is patience helpful?",
                         "Patience gives time for calm thinking, so a problem can be solved without a rushed mistake."))
    else:
        qa.append(QAItem("Why is courage helpful?",
                         "Courage helps an animal speak up for what is right, even when it feels a little scary."))
    return qa


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("parliament", "honesty", "apology", "Milo", "Tessa", "Auntie"),
    StoryParams("parliament", "kindness", "help", "Tessa", "Milo", "Auntie"),
    StoryParams("parliament", "sharing", "share", "Milo", "Tessa", "Auntie"),
    StoryParams("parliament", "patience", "wait", "Tessa", "Milo", "Auntie"),
    StoryParams("parliament", "courage", "speak", "Milo", "Tessa", "Auntie"),
]


def explain_rejection(value: Value, offer: Offer) -> str:
    return f"(No story: the moral value {value.label} does not fit the offer {offer.label} in this parliament tale.)"


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("value", vid) for vid in VALUES]
    lines += [asp.fact("offer", oid) for oid in OFFERS]
    lines += [asp.fact("reasonable_value", vid) for vid in VALUES if vid in {"honesty", "kindness", "sharing", "patience", "courage"}]
    lines += [asp.fact("reasonable_offer", oid) for oid in OFFERS if oid in {"apology", "help", "share", "wait", "speak"}]
    return "\n".join(lines)


ASP_RULES = r"""
good(V,O) :- value(V), offer(O), reasonable_value(V), reasonable_offer(O).
valid_story(S,V,O) :- setting(S), good(V,O).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal parliament storyworld with a moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--elder")
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
    if args.value and args.offer and not is_reasonable(VALUES[args.value], OFFERS[args.offer], SETTINGS["parliament"]):
        raise StoryError(explain_rejection(VALUES[args.value], OFFERS[args.offer]))
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid story combinations.)")
    filtered = [c for c in combos if (args.setting is None or c[0] == args.setting)
                and (args.value is None or c[1] == args.value)
                and (args.offer is None or c[2] == args.offer)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, value, offer = rng.choice(filtered)
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    elder = args.elder or "Auntie"
    return StoryParams(setting, value, offer, hero, friend, elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], VALUES[params.value], OFFERS[params.offer],
                 params.hero, params.friend, params.elder)
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
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
