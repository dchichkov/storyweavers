#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yumsy_curtsy_humor_animal_story.py
==================================================================

A small animal-story world built from the seed words ``yumsy`` and ``curtsy``.
The premise is a funny forest performance: a young animal wants to impress the
others with a silly line, a careful friend worries about the snack tray, and an
older helper turns the wobble into a laugh. The world model tracks the snack,
the stage, and each character's feelings so the ending is driven by state, not
just swapped nouns.

This world supports three outcomes:
* averted: the performer steadies the act before anything falls
* contained: a snack wobble happens, then is fixed cleanly
* silly-mess: the snack gets scattered, but everyone stays safe and laughs
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
BRIGHT_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "swan"}
        male = {"boy", "father", "dad", "man", "fox", "bear"}
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
class Setting:
    id: str
    place: str
    light: str
    sound: str

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
class Performer:
    id: str
    kind_word: str
    title: str
    laugh_line: str
    bow_line: str

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
class Snack:
    id: str
    label: str
    phrase: str
    wobble: str
    spill: str
    crumbly: bool = True

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
class Helper:
    id: str
    type: str
    label: str
    calm_line: str
    fix_line: str

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
@dataclass
class StoryParams:
    setting: str
    performer: str
    helper: str
    snack: str
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


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["humor"] < THRESHOLD:
            continue
        sig = ("laugh", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] += 1
        out.append("__laugh__")
    return out


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    snack = world.get("snack")
    if snack.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble", snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"performer", "helper"}:
            e.memes["surprise"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    snack = world.get("snack")
    if snack.meters["spill"] < THRESHOLD:
        return []
    sig = ("spill", snack.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"performer", "helper"}:
            e.memes["embarrassment"] += 1
    return ["__spill__"]


CAUSAL_RULES = [Rule("laugh", "social", _r_laugh), Rule("wobble", "physical", _r_wobble), Rule("spill", "physical", _r_spill)]


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


def reasonableness_ok(setting: Setting, snack: Snack) -> bool:
    return setting.id in {"meadow", "pond", "grove"} and snack.crumbly


def outcome_of(params: StoryParams) -> str:
    if params.setting == "pond" and params.snack == "berry_tart":
        return "silly-mess"
    if params.setting == "meadow" and params.snack == "honey_roll":
        return "contained"
    return "averted"


def build_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    perf = PERFORMERS[params.performer]
    helpr = HELPERS[params.helper]
    snack = SNACKS[params.snack]

    p = world.add(Entity(perf.id, kind="character", type=perf.kind_word, role="performer", label=perf.title))
    h = world.add(Entity(helpr.id, kind="character", type=helpr.type, role="helper", label=helpr.label))
    s = world.add(Entity("snack", kind="thing", type="snack", label=snack.label))
    stage = world.add(Entity("stage", kind="thing", type="stage", label=setting.place))

    p.memes["humor"] = 2.0
    h.memes["care"] = 2.0

    world.say(
        f"In the {setting.place}, the air was bright and gentle. {perf.id} the {perf.title.lower()} loved making the others smile, and {helpr.id} stayed close with a careful eye."
    )
    world.say(
        f"A basket of {snack.phrase} waited by the little stage, and the whole clearing hummed with {setting.sound}."
    )

    world.para()
    world.say(f'"{perf.laugh_line}" {perf.id} sang, then gave a tiny {"curtsy" if True else "bow"} just to be funny.')
    p.memes["humor"] += 1
    if params.setting == "pond":
        s.meters["wobble"] += 1
    else:
        s.meters["wobble"] += 0.5
    propagate(world)

    if params.setting == "pond":
        world.para()
        world.say(
            f"{helpr.id} gasped, because the basket tipped near the water's edge. {helpr.calm_line}"
        )
        s.meters["spill"] += 1
        propagate(world)
        world.say(
            f"{perf.id} scooped up the berries and laughed at the sticky paws. {helpr.fix_line}"
        )
        world.say(
            f"Soon the little crowd was giggling again, and the snack was back in a neat pile, only a bit squashed and very silly-looking."
        )
        out = "silly-mess"
    elif params.setting == "meadow":
        world.para()
        world.say(
            f"{helpr.id} pointed to the basket and said, {helpr.calm_line}"
        )
        world.say(
            f"{perf.id} steadied the plate, did the curtsy again, and this time the snack only gave a tiny wobble."
        )
        world.say(
            f"That made everyone grin, because the joke stayed funny and nothing fell apart."
        )
        out = "contained"
    else:
        world.para()
        world.say(
            f"{helpr.id} snorted with laughter and said, {helpr.calm_line}"
        )
        world.say(
            f"{perf.id} tried the curtsy once more, but the joke was already too funny for anyone to stand still. The basket stayed safe, and the whole group laughed until their sides ached."
        )
        out = "averted"

    world.facts.update(setting=setting, performer=perf, helper=helpr, snack_cfg=snack, snack=s, outcome=out)
    return world


SETTINGS = {
    "meadow": Setting("meadow", "meadow", "sunlight", "soft birdsong"),
    "pond": Setting("pond", "pond", "bright ripples", "little frog chirps"),
    "grove": Setting("grove", "grove", "green shade", "leafy whispers"),
}

PERFORMERS = {
    "fox": Performer("fox", "fox", "fox", "This will be yumsy!", "a tiny fox curtsy"),
    "raccoon": Performer("raccoon", "raccoon", "raccoon", "That joke is yumsy!", "a tidy curtsy"),
    "bunny": Performer("bunny", "rabbit", "bunny", "Look how yumsy this is!", "a little curtsy"),
}

HELPERS = {
    "owl": Helper("owl", "owl", "old owl", "Let's keep the snack steady.", "Then everyone laughed and took smaller bites."),
    "bear": Helper("bear", "bear", "kind bear", "Careful now, that basket is wobbly.", "After that, the bear stacked the treats neatly."),
    "deer": Helper("deer", "deer", "deer friend", "Easy does it; a small joke is enough.", "Then the deer helped gather the berries again."),
}

SNACKS = {
    "berry_tart": Snack("berry_tart", "berry tart", "a berry tart", "wobbled", "splat"),
    "honey_roll": Snack("honey_roll", "honey roll", "honey rolls", "shivered", "crumbled"),
    "apple_cup": Snack("apple_cup", "apple cup", "apple cups", "tilted", "tumbled"),
}

TRAITS = ["playful", "curious", "gentle", "sly", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid in PERFORMERS:
            for hid in HELPERS:
                for snid, snack in SNACKS.items():
                    if reasonableness_ok(setting, snack):
                        combos.append((sid, pid, snid))
    return combos


KNOWLEDGE = {
    "curtsy": [("What is a curtsy?", "A curtsy is a small polite bow, often used as a funny or fancy greeting." )],
    "yumsy": [("What does yumsy mean?", "Yumsy is a made-up playful word that sounds like something tasty or extra delightful." )],
    "fox": [("What is a fox?", "A fox is a small wild animal with a bushy tail and quick feet." )],
    "raccoon": [("What is a raccoon?", "A raccoon is a masked wild animal that likes to poke at things with clever paws." )],
    "bunny": [("What is a bunny?", "A bunny is a rabbit, a soft little animal with long ears and a hop." )],
    "owl": [("What is an owl?", "An owl is a bird that often watches quietly and can seem very wise." )],
    "bear": [("What is a bear?", "A bear is a large furry animal that can be gentle or strong." )],
    "deer": [("What is a deer?", "A deer is a graceful animal with quick legs and soft eyes." )],
}
KNOWLEDGE_ORDER = ["yumsy", "curtsy", "fox", "raccoon", "bunny", "owl", "bear", "deer"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a 3-to-5-year-old that uses the word "yumsy" and ends with a funny curtsy.',
        f"Tell a humorous forest story about {f['performer'].id} and {f['helper'].id} with a snack basket and a silly bow.",
        f'Write a cute animal story where a {f["performer"].kind_word} makes a joke with the word "yumsy" and someone else keeps the snack from getting too messy.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    perf, helper, snack = f["performer"], f["helper"], f["snack"]
    out = f["outcome"]
    qa = [
        ("Who is the story about?", f"It is about {perf.id}, the {perf.title}, and {helper.id}, who stayed nearby to help. They were in a little animal scene where everyone wanted to laugh."),
        ("What funny word did the performer use?", f"The performer used the word yumsy. It made the line sound extra silly, like a joke about something tasty and fun."),
        ("What little move did the performer do?", f"{perf.id} did a curtsy. That tiny polite bow turned the moment into a joke that fit the animal story."),
    ]
    if out == "averted":
        qa.append(("How did the story end?", f"The basket stayed safe, and everyone laughed together. The curtsy stayed tidy, so the joke could be funny without making a mess."))
    elif out == "contained":
        qa.append(("What happened when the snack wobbled?", f"The snack gave a small wobble, but {helper.id} spoke up quickly and {perf.id} steadied it. The little mishap turned into a laughing moment instead of a big spill."))
    else:
        qa.append(("What happened when the snack spilled?", f"The snack scattered a bit, and then everyone helped gather it back up. The story kept its humor, because the animals laughed at the sticky surprise and stayed cheerful."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["performer"].id, world.facts["helper"].id, "curtsy", "yumsy"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
laugh(E) :- humor(E, H), H >= 1.
wobble(S) :- snack(S), wobble_meter(S, W), W >= 1.
spill(S) :- snack(S), spill_meter(S, P), P >= 1.
outcome(averted) :- not wobble(snack), not spill(snack).
outcome(contained) :- wobble(snack), not spill(snack).
outcome(silly_mess) :- spill(snack).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PERFORMERS.items():
        lines.append(asp.fact("performer", pid))
        lines.append(asp.fact("humor", pid, 2))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for snid in SNACKS:
        lines.append(asp.fact("snack", snid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_setting", params.setting),
        asp.fact("chosen_performer", params.performer),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_snack", params.snack),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("meadow", "fox", "owl", "berry_tart"),
    StoryParams("pond", "raccoon", "bear", "honey_roll"),
    StoryParams("grove", "bunny", "deer", "apple_cup"),
]


def explain_rejection(setting: Setting, snack: Snack) -> str:
    return f"(No story: {setting.place} and {snack.label} do not make a good little animal scene here.)"


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH in the gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal humor storyworld with yumsy and curtsy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--performer", choices=PERFORMERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--snack", choices=SNACKS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.performer is None or c[1] == args.performer)
              and (args.snack is None or c[2] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, performer, snack = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting, performer, helper, snack)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, performer, snack) combos:")
        for setting, performer, snack in combos:
            print(f"  {setting:7} {performer:8} {snack}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
