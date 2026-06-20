#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cumbersome_actor_allergy_sharing_cautionary_adventure.py
=======================================================================================

A standalone story world about a small adventure in a theater club:
children carry a very cumbersome costume prop to a show, one child has an
allergy, the group realizes a shared snack or prop could cause trouble, and a
careful swap leads to a safer, happier adventure.

The domain is built from the seed words:
- cumbersome
- actor
- allergy

And the requested features:
- Sharing
- Cautionary
- Adventure

This script follows the Storyweavers storyworld contract:
- stdlib-only
- imports storyworlds/results.py eagerly
- includes StoryParams, registries, build_parser, resolve_params, generate,
  emit, main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n,
  --seed
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
from typing import Optional

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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    adventure: str
    detail: str

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
class Item:
    id: str
    label: str
    phrase: str
    detail: str
    cumbersome: bool = False
    shared: bool = False
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
class Allergy:
    id: str
    label: str
    trigger: str
    symptom: str
    warning: str
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
class Aid:
    id: str
    label: str
    phrase: str
    action: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "backstage": Setting("backstage", "the backstage corridor", "a treasure hunt", "The hall was full of curtains, ropes, and painted boards."),
    "harbor": Setting("harbor", "the harbor pier", "a map quest", "The pier smelled like salt and old wood."),
    "garden": Setting("garden", "the old garden path", "a lantern walk", "The path bent between hedges and stone steps."),
}

ITEMS = {
    "mask": Item("mask", "mask", "a bright paper mask", "It was bright, but its ribbons were cumbersome to carry.", cumbersome=True, shared=True, tags={"mask", "cumbersome"}),
    "cape": Item("cape", "cape", "a long costume cape", "It swept the floor and snagged on corners.", cumbersome=True, shared=True, tags={"cape", "cumbersome"}),
    "basket": Item("basket", "basket of snacks", "a basket of shared snacks", "It was easy to pass around, but not every snack was safe.", shared=True, tags={"sharing"}),
}

ALLERGIES = {
    "peanut": Allergy("peanut", "peanut allergy", "peanuts", "itchy throat", "Peanuts could make the child sneeze and feel scared.", tags={"allergy", "peanut"}),
    "dairy": Allergy("dairy", "milk allergy", "milk", "tummy pain", "Milk could make the child feel sick.", tags={"allergy", "dairy"}),
}

AIDS = {
    "fruit": Aid("fruit", "fruit bowl", "a bowl of sliced apples and grapes", "choose fruit instead of the unsafe snack", tags={"sharing"}),
    "label": Aid("label", "tiny labels", "tiny stickers with names on them", "mark each snack before sharing", tags={"sharing", "cautionary"}),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Ava", "Nora", "Ruby", "Lila"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Leo", "Finn", "Owen", "Jasper"]


def hazard(item: Item, allergy: Allergy) -> bool:
    return item.shared and allergy.trigger in {"peanuts", "milk"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for i in ITEMS:
            for a in ALLERGIES:
                if hazard(ITEMS[i], ALLERGIES[a]):
                    out.append((s, i, a))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    allergy: str
    aid: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    adult: str
    seed: Optional[int] = None

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with sharing and caution around allergies.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--allergy", choices=ALLERGIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    if args.item and args.allergy and not hazard(ITEMS[args.item], ALLERGIES[args.allergy]):
        raise StoryError("That item and allergy do not make a real cautionary problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.allergy is None or c[2] == args.allergy)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    setting, item, allergy = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend_name or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(setting, item, allergy, aid, hero, hero_gender, friend, friend_gender, adult)


def _propagate(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    allergy = world.facts["allergy_cfg"]
    item = world.facts["item_cfg"]
    if child.meters["exposed"] >= THRESHOLD and allergy.trigger in {"peanuts", "milk"}:
        sig = ("symptom", allergy.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            child.meters["sneezing"] += 1
            if narrate:
                world.say(f"{child.id} sniffled and rubbed {child.pronoun('possessive')} nose.")


def tell(setting: Setting, item: Item, allergy: Allergy, aid: Aid, hero: str, hero_gender: str, friend: str, friend_gender: str, adult: str) -> World:
    world = World()
    child = world.add(Entity("child", "character", hero_gender, role="hero"))
    child.id = hero
    child.type = hero_gender
    friend_ent = world.add(Entity("friend", "character", friend_gender, role="helper"))
    friend_ent.id = friend
    friend_ent.type = friend_gender
    parent = world.add(Entity("adult", "character", adult, role="adult", label="the adult"))
    world.facts.update(setting=setting, item_cfg=item, allergy_cfg=allergy, aid_cfg=aid, adult=parent)
    child.memes["curiosity"] += 1
    friend_ent.memes["care"] += 1
    world.say(f"{hero} and {friend} began their adventure near {setting.place}. {setting.detail}")
    world.say(f"They found {item.phrase}, and {item.detail}")
    world.say(f'{hero} said, "It would be fun to share it on the trail."')
    world.para()
    world.say(f"But {friend} noticed a warning card in {setting.place}: {allergy.warning}")
    world.say(f'{friend} bit {friend_ent.pronoun("possessive")} lip and said, "Wait. {allergy.label.capitalize()} can cause trouble."')
    world.say(f'{hero} felt the weight of the cumbersome prop and slowed down.')
    if item.shared and allergy.trigger in {"peanuts", "milk"}:
        child.meters["exposed"] += 1
        if item.id == "basket":
            world.say(f"The shared basket made it easy for everyone to reach in at once, which was risky.")
    _propagate(world, narrate=True)
    world.para()
    if item.shared and allergy.trigger in {"peanuts", "milk"}:
        world.say(f"{adult.capitalize()} came over and agreed with {friend}.")
        world.say(f'Together they chose {aid.phrase}, so the group could {aid.action}.')
        child.memes["relief"] += 1
        friend_ent.memes["joy"] += 1
        world.say(f"{hero} smiled, and the adventure continued with safe treats and careful hands.")
    else:
        world.say(f"The little adventure stayed easy and calm, and everyone kept sharing safely.")
    world.facts.update(hero=child, friend=friend_ent, outcome="cautious", shared=item.shared)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly adventure story that includes the words "cumbersome" and "allergy" and shows children sharing carefully.',
        f'Tell a cautionary adventure where {f["hero"].id} and {f["friend"].id} notice a sharing problem and choose a safer way.',
        f'Write a short story about a cumbersome costume prop, a warning, and a thoughtful shared replacement.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    allergy = f["allergy_cfg"]
    item = f["item_cfg"]
    aid = f["aid_cfg"]
    qas = [
        QAItem(
            question=f"Why did {friend.id} warn {hero.id}?",
            answer=f"{friend.id} noticed that {allergy.label} could cause trouble, so {friend.id} spoke up before the shared item caused a problem. That caution kept the adventure safe."
        ),
        QAItem(
            question=f"What made the costume prop hard to carry?",
            answer=f"It was cumbersome, which meant it was awkward and a little heavy to handle. That is why the children slowed down and thought before rushing ahead."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"{adult.id} and the children chose {aid.label} instead, so they could keep sharing without the risky snack or prop. The safer choice let the adventure continue happily."
        ),
    ]
    if item.id == "basket":
        qas.append(QAItem(
            question="Why was the basket risky?",
            answer="The basket held shared snacks, so everyone could reach in together. That made it important to check allergies before anyone ate."
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["item_cfg"].tags) | set(world.facts["allergy_cfg"].tags) | set(world.facts["aid_cfg"].tags)
    out: list[QAItem] = []
    if "cumbersome" in tags:
        out.append(QAItem("What does cumbersome mean?", "Cumbersome means hard to carry, handle, or move because it is awkward or heavy. A cumbersome thing can slow you down on an adventure."))
    if "allergy" in tags:
        out.append(QAItem("What is an allergy?", "An allergy is when a person's body reacts badly to certain things, like some foods. If someone has an allergy, they must be careful about what they touch or eat."))
    if "sharing" in tags:
        out.append(QAItem("What does it mean to share safely?", "Sharing safely means thinking about what other people need and making sure the thing is okay for them. Careful sharing helps everyone stay included and protected."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(I, A) :- item(I), allergy(A), shared(I), trigger(A, T), relevant(T).
valid(S, I, A) :- setting(S), hazard(I, A).
outcome(cautious) :- valid(_, _, _).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i, item in ITEMS.items():
        lines.append(asp.fact("item", i))
        if item.shared:
            lines.append(asp.fact("shared", i))
    for a, allergy in ALLERGIES.items():
        lines.append(asp.fact("allergy", a))
        lines.append(asp.fact("trigger", a, allergy.trigger))
        lines.append(asp.fact("relevant", allergy.trigger))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            print("MISMATCH: ASP and Python valid_combos differ.")
            rc = 1
        else:
            print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal story generation works.")
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        return 1
    return rc


def explain_rejection(item: Item, allergy: Allergy) -> str:
    return f"(No story: {item.label} does not create a useful allergy problem with {allergy.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")
    if args.item and args.allergy and not hazard(ITEMS[args.item], ALLERGIES[args.allergy]):
        raise StoryError(explain_rejection(ITEMS[args.item], ALLERGIES[args.allergy]))
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.item is None or c[1] == args.item) and (args.allergy is None or c[2] == args.allergy)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, item, allergy = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend_name or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(setting, item, allergy, aid, hero, hero_gender, friend, friend_gender, adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], ALLERGIES[params.allergy], AIDS[params.aid], params.hero, params.hero_gender, params.friend, params.friend_gender, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("backstage", "basket", "peanut", "fruit", "Mia", "girl", "Theo", "boy", "mother"),
        StoryParams("harbor", "cape", "dairy", "label", "Leo", "boy", "Nora", "girl", "father"),
        StoryParams("garden", "mask", "peanut", "fruit", "Ava", "girl", "Ben", "boy", "mother"),
    ]


CURATED = build_curated()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
