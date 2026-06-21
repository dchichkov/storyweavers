#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/attract_thingamajig_bad_ending_tall_tale.py
============================================================================

A tiny tall-tale storyworld about a foolish contraption, a barnyard prank, and a
bad ending when the "attract" gizmo pulls in far too much trouble.

Seed words:
- attract
- thingamajig

Style:
- Tall tale

Feature:
- Bad ending
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Character:
    id: str
    type: str
    role: str
    title: str
    brave: int = 0
    cautious: int = 0
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
        return self.title
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Thingamajig:
    id: str
    label: str
    catch_phrase: str
    place: str
    effect: str
    makes_noise: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Target:
    id: str
    label: str
    kind: str
    flock: str
    startle: str
    danger: int
    attracted_by: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    device: str
    target: str
    hero: str
    hero_gender: str
    sidekick: str
    sidekick_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_attract(world: World) -> list[str]:
    out: list[str] = []
    for obj in list(world.entities.values()):
        if not isinstance(obj, Thingamajig):
            continue
        if obj.meters["humming"] < THRESHOLD:
            continue
        sig = ("attract", obj.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if isinstance(ent, Target):
                ent.meters["drawn"] += 1
                if obj.label in ent.attracted_by:
                    ent.meters["drawn"] += 1
        out.append("__attract__")
    return out


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    for tgt in list(world.entities.values()):
        if not isinstance(tgt, Target):
            continue
        if tgt.meters["drawn"] < THRESHOLD:
            continue
        sig = ("trouble", tgt.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in list(world.entities.values()):
            if isinstance(ent, Character):
                ent.memes["alarm"] += 1
        out.append("__trouble__")
    return out


RULES = [Rule("attract", _r_attract), Rule("trouble", _r_trouble)]


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    for s in out:
        world.say(s)
    return out


def badness(target: Target) -> int:
    return target.danger


def can_fit(device: Thingamajig, target: Target) -> bool:
    return device.label in target.attracted_by


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for did, d in DEVICES.items():
        if d.makes_noise:
            for tid, t in TARGETS.items():
                if can_fit(d, t):
                    combos.append((did, tid))
    return combos


def reasonableness_gate(device: Thingamajig, target: Target) -> None:
    if not device.makes_noise:
        raise StoryError("No story: the thingamajig must make a racket for a tall tale.")
    if not can_fit(device, target):
        raise StoryError(
            f"No story: {device.label} won't attract {target.label}, so nothing grand can go wrong."
        )


def _pronoun_name(ent) -> str:
    return ent.id


def tell(device: Thingamajig, target: Target, hero: Character, sidekick: Character, adult: Character) -> World:
    w = World()
    w.add(copy.deepcopy(hero))
    w.add(copy.deepcopy(sidekick))
    w.add(copy.deepcopy(adult))
    dev = w.add(copy.deepcopy(device))
    tgt = w.add(copy.deepcopy(target))

    hero.memes["hope"] += 1
    sidekick.memes["wonder"] += 1
    w.say(
        f"On a wind-chewed afternoon, {hero.id} and {sidekick.id} found "
        f"{device.label} in the barn loft. It was a great, tinny thingamajig, "
        f"all springs and whistles, fit to make a mule blink."
    )
    w.say(
        f'"This little {device.label} will attract {target.label} from the far side '
        f"of the county," {hero.id} boasted, and {sidekick.id} laughed like a kettle."
    )
    w.para()
    w.say(
        f"But {target.label} were already hungry for nonsense, and that old {device.label} "
        f"sat there humming its {device.catch_phrase} from {device.place}."
    )
    dev.meters["humming"] += 1
    propagate(w)
    if tgt.meters["drawn"] >= THRESHOLD:
        w.say(
            f"Before anybody could sneeze, {target.label} came pounding in. "
            f"They knocked over the feed pail, splashed through the yard, and set "
            f"the whole picnic clattering."
        )
        w.para()
        w.say(
            f"{adult.label_word.capitalize()} came running, but the kerfuffle had grown tall as a corn stalk. "
            f"{adult.id} shouted for them to shut the thingamajig off, only the lever stuck fast."
        )
        w.say(
            f"The device yowled, the {target.label} scattered every which way, and the best-laid plan turned to dust."
        )
        for ent in (hero, sidekick):
            ent.memes["regret"] += 1
        w.say(
            f"By sundown, {hero.id} and {sidekick.id} were sweeping splinters off the porch while the "
            f"thingamajig sat silent as a stone. Nobody called it clever after that."
        )
    else:
        w.say("But nothing much happened, which is no tall tale at all.")
    w.facts.update(hero=hero, sidekick=sidekick, adult=adult, device=device, target=target, outcome="bad")
    return w


HEROES = [
    ("Finn", "boy"),
    ("Mabel", "girl"),
    ("Jasper", "boy"),
    ("Nell", "girl"),
]
ADULTS = [
    ("Aunt June", "woman"),
    ("Uncle Ben", "man"),
    ("Ma", "woman"),
    ("Pa", "man"),
]
DEVICES = {
    "whistler": Thingamajig(
        id="whistler",
        label="whistler",
        catch_phrase="wheee-ooo",
        place="the porch",
        effect="a bright old whistle",
    ),
    "bugle": Thingamajig(
        id="bugle",
        label="bugle-box",
        catch_phrase="toot-toot",
        place="the shed",
        effect="a hollow brass honk",
    ),
}
TARGETS = {
    "mules": Target(
        id="mules",
        label="mules",
        kind="animals",
        flock="a mule team",
        startle="stamped and snorted",
        danger=3,
        attracted_by={"whistler", "bugle-box"},
    ),
    "geese": Target(
        id="geese",
        label="geese",
        kind="animals",
        flock="a goose gang",
        startle="honked and flapped",
        danger=2,
        attracted_by={"whistler", "bugle-box"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with a bad ending.")
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["boy", "girl"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["man", "woman"])
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
              if (args.device is None or c[0] == args.device)
              and (args.target is None or c[1] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    device, target = rng.choice(sorted(combos))
    hero_name, hero_gender = (args.hero, args.hero_gender) if args.hero and args.hero_gender else rng.choice(HEROES)
    sidekick_name, sidekick_gender = (args.sidekick, args.sidekick_gender) if args.sidekick and args.sidekick_gender else rng.choice([h for h in HEROES if h[0] != hero_name])
    adult_name, adult_gender = (args.adult, args.adult_gender) if args.adult and args.adult_gender else rng.choice(ADULTS)
    return StoryParams(
        device=device,
        target=target,
        hero=hero_name,
        hero_gender=hero_gender,
        sidekick=sidekick_name,
        sidekick_gender=sidekick_gender,
        adult=adult_name,
        adult_gender=adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.device not in DEVICES or params.target not in TARGETS:
        raise StoryError("Invalid params.")
    device = DEVICES[params.device]
    target = TARGETS[params.target]
    reasonableness_gate(device, target)
    hero = Character(id=params.hero, type=params.hero_gender, role="hero", title="the tall-tale hero")
    sidekick = Character(id=params.sidekick, type=params.sidekick_gender, role="sidekick", title="the sidekick")
    adult = Character(id=params.adult, type=params.adult_gender, role="adult", title="the grown-up")
    world = tell(device, target, hero, sidekick, adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a young child that includes the words "attract" and "thingamajig".',
        f"Tell a silly barnyard story where {f['hero'].id} uses a thingamajig to attract {f['target'].label}, and it goes badly wrong.",
        f"Write a bad-ending tall tale about a noisy contraption, a reckless plan, and a ruined barnyard afternoon.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    adult = f["adult"]
    target = f["target"]
    return [
        ("What did the children find in the barn loft?",
         f"They found a thingamajig, a noisy little contraption that looked too proud of itself. It was the sort of gadget a tall tale would use to stir up trouble."),
        (f"What did {hero.id} try to do with it?",
         f"{hero.id} tried to attract {target.label} with it. That was the whole foolish plan, and it is why the trouble grew so fast."),
        (f"Why did the plan end badly?",
         f"The thingamajig made enough racket to draw {target.label} in, and they charged the yard and spilled everything. The grown-up could not stop the mess before it got big."),
        ("How did the story end?",
         f"It ended badly, with the device ruined and the children sweeping up the wreckage. The tall-tale fun turned into a lesson they would not forget."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a thingamajig?",
         "A thingamajig is a made-up word for a gadget when someone does not want to name it exactly. People often use it for a funny or strange contraption."),
        ("What does attract mean?",
         "To attract something means to pull it toward you or make it come closer. A loud sound, a smell, or a bright light can attract animals or people."),
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
        if hasattr(e, "label") and getattr(e, "label"):
            bits.append(f"label={getattr(e, 'label')}")
        lines.append(f"  {e.id:10} ({getattr(e, 'type', 'thing'):7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        device="whistler",
        target="geese",
        hero="Nell",
        hero_gender="girl",
        sidekick="Finn",
        sidekick_gender="boy",
        adult="Aunt June",
        adult_gender="woman",
    ),
    StoryParams(
        device="bugle",
        target="mules",
        hero="Jasper",
        hero_gender="boy",
        sidekick="Mabel",
        sidekick_gender="girl",
        adult="Uncle Ben",
        adult_gender="man",
    ),
]


ASP_RULES = r"""
noise(D) :- thingamajig(D), makes_noise(D).
attracts(D,T) :- noise(D), target(T), linked(D,T).
trouble(T) :- attracts(D,T), target(T).
bad_end :- trouble(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for did, d in DEVICES.items():
        lines.append(asp.fact("thingamajig", did))
        if d.makes_noise:
            lines.append(asp.fact("makes_noise", did))
        for tid in TARGETS:
            if d.label in TARGETS[tid].attracted_by:
                lines.append(asp.fact("linked", did, tid))
    for tid in TARGETS:
        lines.append(asp.fact("target", tid))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show linked/2."))
    return sorted(set(asp.atoms(model, "linked")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((d, t) for d, t in valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    if rc == 0:
        print("OK: ASP/Python parity and generate() smoke test passed.")
    return rc


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
        print(asp_program("#show linked/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} -> {b}" for a, b in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
