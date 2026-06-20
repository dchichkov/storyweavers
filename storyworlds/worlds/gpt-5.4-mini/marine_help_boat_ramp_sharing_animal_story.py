#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/marine_help_boat_ramp_sharing_animal_story.py
=============================================================================

A standalone story world for a small animal-story domain at a boat ramp.

Premise:
- A few animals are at a boat ramp on a bright day.
- One animal has a box of marine supplies and sees another animal who needs help.
- The group practices sharing, so they pass the useful gear around.
- The helpful choice makes the launch go smoothly and ends with a calm shared boat ride.

This world keeps the story small, concrete, and state-driven:
- typed entities with physical meters and emotional memes
- a reasonableness gate for the valid setup
- a tiny forward-chained world model
- three QA sets grounded in the simulated world
- an inline ASP twin with parity verification

Seed words honored in the domain: marine, help.
Setting: boat ramp.
Feature: sharing.
Style: animal story.
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
SHARE_MIN = 2


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
        return self.label or self.type



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
    afford: set[str] = field(default_factory=set)

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
class Need:
    id: str
    label: str
    phrase: str
    place_hint: str
    needed_for: str
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
class ShareItem:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
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
        return clone

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


def _r_need_help(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role != "helper":
            continue
        if ent.meters["need_help"] < THRESHOLD:
            continue
        sig = ("need_help", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("")
    return out


def _r_sharing_cheer(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared") and not world.facts.get("cheer_rule_done"):
        world.facts["cheer_rule_done"] = True
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["joy"] += 1
        out.append("")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("need_help", "social", _r_need_help),
    Rule("sharing_cheer", "social", _r_sharing_cheer),
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
                produced.extend([s for s in sents if s])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def simple_reasonable(items: list[tuple[str, str, str]]) -> list[tuple[str, str, str]]:
    return items


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for need_id, need in NEEDS.items():
            for item_id, item in SHARES.items():
                if need_id in item.helps_with and setting_id in setting.afford:
                    combos.append((setting_id, need_id, item_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    need: str
    share_item: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    marine_friend: str
    marine_friend_gender: str
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


def setup(world: World, hero: Entity, helper: Entity, marine_friend: Entity,
          need: Need, item: ShareItem) -> None:
    world.say(
        f"At the boat ramp, {hero.id} and {helper.id} were helping "
        f"{marine_friend.id} get ready for a small trip. "
        f"The water tapped the pilings, and the ramp smelled salty and bright."
    )
    world.say(
        f"{marine_friend.id} needed {need.phrase}, and {hero.id} held up "
        f"{item.phrase} with a careful smile."
    )


def show_need(world: World, helper: Entity, marine_friend: Entity, need: Need) -> None:
    helper.meters["need_help"] += 1
    helper.memes["worry"] += 1
    world.say(
        f'"We need some help," {marine_friend.id} called. '
        f"One strap was loose, and the little boat leaned near the dock."
    )
    world.say(
        f"{helper.id} looked at the gear and said, "
        f'"This will be easier if we share what we have."'
    )


def share(world: World, giver: Entity, helper: Entity, item: ShareItem, need: Need) -> None:
    giver.memes["generous"] += 1
    helper.memes["trust"] += 1
    world.facts["shared"] = True
    world.say(
        f"{giver.id} passed {item.phrase} to {helper.id}, and {helper.id} used it to "
        f"{need.needed_for}."
    )


def launch(world: World, hero: Entity, helper: Entity, marine_friend: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    marine_friend.memes["relief"] += 1
    world.say(
        f"Soon the three animals pushed the boat together. It slid from the ramp "
        f"and floated straight and steady."
    )
    world.say(
        f"{marine_friend.id} grinned, {hero.id} waved, and {helper.id} tucked the "
        f"shared gear safely back into the box."
    )


def tell(setting: Setting, need: Need, item: ShareItem,
         hero_name: str = "Milo", hero_gender: str = "boy",
         helper_name: str = "Nina", helper_gender: str = "girl",
         marine_friend_name: str = "Otter", marine_friend_gender: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="giver"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    marine_friend = world.add(Entity(
        id=marine_friend_name, kind="character", type=marine_friend_gender, role="friend"
    ))
    box = world.add(Entity(id="box", label="marine help box"))
    box.meters["full"] = 1
    hero.attrs["box"] = box.id

    setup(world, hero, helper, marine_friend, need, item)
    world.para()
    show_need(world, helper, marine_friend, need)
    share(world, hero, helper, item, need)
    world.para()
    propagate(world, narrate=False)
    launch(world, hero, helper, marine_friend)

    world.facts.update(
        setting=setting, need=need, item=item,
        hero=hero, helper=helper, marine_friend=marine_friend,
        shared=True, outcome="shared_help",
    )
    return world


SETTINGS = {
    "boatramp": Setting(
        "boatramp",
        "the boat ramp",
        "The ramp sloped into the water, and a small dock waited beside it.",
        afford={"line", "lift", "guide"},
    ),
    "shore": Setting(
        "shore",
        "the boat ramp by the shore",
        "The shore was breezy, and gulls bobbed over the wet boards.",
        afford={"line", "lift", "guide"},
    ),
}

NEEDS = {
    "line": Need("line", "a rope line", "a rope line", "tie the boat to the dock", "line the boat up", {"rope", "help"}),
    "lift": Need("lift", "a lifting strap", "a lifting strap", "steady the boat on the ramp", "lift the boat together", {"strap", "help"}),
    "guide": Need("guide", "a guiding pole", "a guiding pole", "guide the boat away from the rocks", "guide the boat safely", {"pole", "help"}),
}

SHARES = {
    "rope": ShareItem("rope", "a rope", "a long rope", {"line"}, {"rope", "sharing", "marine"}),
    "strap": ShareItem("strap", "a strap", "a sturdy strap", {"lift"}, {"strap", "sharing", "marine"}),
    "pole": ShareItem("pole", "a pole", "a smooth guiding pole", {"guide"}, {"pole", "sharing", "marine"}),
}

GIRL_NAMES = ["Nina", "Luna", "Maya", "Ivy", "Ruby", "Zoe"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Owen", "Kai", "Noah"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a 3-to-5-year-old set at {f["setting"].place} that includes the words "marine" and "help".',
        f"Tell a gentle story where {f['hero'].id}, {f['helper'].id}, and {f['marine_friend'].id} share a useful tool so the boat can launch safely.",
        f'Write a small sharing story about animals at the boat ramp, ending with a calm boat ride and the word "marine".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, friend = f["hero"], f["helper"], f["marine_friend"]
    item, need = f["item"], f["need"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, {helper.id}, and {friend.id}, three animals at the boat ramp who worked together."),
        ("What did they need?",
         f"They needed {need.phrase} so the boat could be ready to launch. The helpful tool made the job easier."),
        ("How did they solve the problem?",
         f"{hero.id} shared {item.phrase} with {helper.id}, and {helper.id} used it to {need.needed_for}. That sharing gave everyone a hand."),
        ("How did the story end?",
         f"The boat slid into the water safely, and the animals felt proud and happy. The shared gear went back in the box, ready for the next helper."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"marine", "help", "sharing", world.facts["need"].id, world.facts["item"].id}
    out: list[tuple[str, str]] = []
    if "marine" in tags:
        out.append(("What does marine mean?",
                    "Marine means connected to the sea, the water, or sea animals. It is a word people use for things that belong near the ocean or in the water."))
    if "help" in tags:
        out.append(("What does it mean to help?",
                    "To help means to do something that makes a job easier for someone else. Helping can mean sharing tools, lifting, or showing kindness."))
    if "sharing" in tags:
        out.append(("What is sharing?",
                    "Sharing means letting someone else use something you have. It is a kind way to work together and solve a problem."))
    if world.facts["need"].id == "line":
        out.append(("What is a rope line for?",
                    "A rope line helps tie or guide a boat so it stays where it should. People use it to keep a boat steady near a dock or ramp."))
    if world.facts["need"].id == "lift":
        out.append(("What is a lifting strap for?",
                    "A lifting strap helps people carry or steady something heavy together. It gives a better grip so a job is safer and easier."))
    if world.facts["need"].id == "guide":
        out.append(("What is a guiding pole for?",
                    "A guiding pole helps steer something gently in the right direction. It is useful when something needs a little careful help."))
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, N, I) :- setting(S), need(N), item(I), setting_affords(S, N), item_helps(I, N).
shared_help :- valid(S, N, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("setting_affords", sid, a))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for iid, it in SHARES.items():
        lines.append(asp.fact("item", iid))
        for n in sorted(it.helps_with):
            lines.append(asp.fact("item_helps", iid, n))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0
    if a == b:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate:")
        print("  only in ASP:", sorted(a - b))
        print("  only in Python:", sorted(b - a))
    # smoke test
    try:
        p = resolve_params(build_parser().parse_args([]), random.Random(7))
        s = generate(p)
        assert s.story.strip()
        assert s.prompts and s.story_qa and s.world_qa
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world at a boat ramp about marine help and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--item", choices=SHARES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--marine-friend")
    ap.add_argument("--marine-friend-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.need is None or c[1] == args.need)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, need, item = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    marine_friend_gender = args.marine_friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    marine_friend = args.marine_friend or _pick_name(rng, marine_friend_gender, avoid=hero)
    return StoryParams(setting, need, item, hero, hero_gender, helper, helper_gender, marine_friend, marine_friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], NEEDS[params.need], SHARES[params.item],
                 params.hero, params.hero_gender,
                 params.helper, params.helper_gender,
                 params.marine_friend, params.marine_friend_gender)
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


CURATED = [
    StoryParams("boatramp", "line", "rope", "Milo", "boy", "Nina", "girl", "Otter", "boy"),
    StoryParams("shore", "lift", "strap", "Luna", "girl", "Theo", "boy", "Seal", "girl"),
    StoryParams("boatramp", "guide", "pole", "Ivy", "girl", "Kai", "boy", "Pip", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}, {p.helper}, and {p.marine_friend}: {p.setting} / {p.need} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
