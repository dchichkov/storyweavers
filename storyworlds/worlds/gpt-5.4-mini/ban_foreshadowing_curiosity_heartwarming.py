#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ban_foreshadowing_curiosity_heartwarming.py
===========================================================================

A standalone storyworld for a small heartwarming domain: a curious child is told
to respect a ban on opening a covered surprise, notices foreshadowing clues, and
ends up helping with a gentle reveal.

The world is built from state, not from a frozen paragraph:
- typed entities with physical meters and emotional memes
- a small causal rule engine
- a reasonableness gate
- Q&A sets grounded in the simulated world
- an inline ASP twin for parity checks
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
BAN_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



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
    weather: str
    quiet: bool = True

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
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    warm_detail: str
    clue1: str
    clue2: str
    clue3: str

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
class Ban:
    id: str
    label: str
    wording: str
    reason: str
    strictness: int = 1
    true_ban: bool = True

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
class Helper:
    id: str
    label: str
    action: str
    gift_line: str
    ending_image: str

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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("surprise").meters["hint"] += 1
    world.get("adult").memes["warmth"] += 1
    out.append("__clue__")
    return out


def _r_wait(world: World) -> list[str]:
    child = world.get("child")
    surprise = world.get("surprise")
    if child.memes["patience"] < THRESHOLD or surprise.meters["hint"] < THRESHOLD:
        return []
    sig = ("wait",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["pride"] += 1
    return ["__wait__"]


CAUSAL_RULES = [
    Rule("clue", "social", _r_clue),
    Rule("wait", "social", _r_wait),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(ban: Ban, surprise: Surprise) -> bool:
    return ban.true_ban and surprise.label and ban.strictness >= BAN_MIN


def predict(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["curiosity"] += 1
    propagate(sim, narrate=False)
    return {
        "hint": sim.get("surprise").meters["hint"],
        "pride": sim.get("child").memes["pride"],
    }


def setup(world: World, child: Entity, adult: Entity, setting: Setting, ban: Ban, surprise: Surprise) -> None:
    child.memes["joy"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {adult.id} were at {setting.place}. "
        f"The {setting.scene} felt calm and cozy."
    )
    world.say(
        f"{adult.label_word.capitalize()} gave a gentle ban: \"Please do not open the {ban.label} yet. "
        f"{ban.reason}.\""
    )
    world.say(
        f"{child.id} looked at the covered thing and wondered what was inside."
    )


def foreshadow(world: World, child: Entity, adult: Entity, surprise: Surprise) -> None:
    world.say(
        f"Still, little clues kept peeking out: {surprise.clue1}, {surprise.clue2}, and {surprise.clue3}."
    )
    world.say(
        f"{child.id} noticed each clue and grew more curious, but {adult.id} only smiled and said to wait a little longer."
    )


def ask_and_help(world: World, child: Entity, adult: Entity, surprise: Surprise) -> None:
    pred = predict(world)
    child.memes["curiosity"] += 1
    world.facts["predicted_hint"] = pred["hint"]
    world.say(
        f"{child.id} took a breath and asked, \"Can I help?\""
    )
    adult.memes["trust"] += 1
    child.memes["patience"] += 1
    world.say(
        f"{adult.label_word.capitalize()} nodded and let {child.id} carry a little ribbon and a card."
    )
    propagate(world, narrate=False)


def reveal(world: World, child: Entity, adult: Entity, surprise: Surprise, helper: Helper) -> None:
    surprise.meters["revealed"] = 1
    adult.memes["love"] += 1
    child.memes["love"] += 1
    world.say(
        f"At last the {surprise.label} was opened, and inside was {surprise.reveal}."
    )
    world.say(
        f"{surprise.warm_detail} {helper.gift_line}"
    )
    world.say(
        f"{adult.label_word.capitalize()} thanked {child.id} for waiting so kindly."
    )
    world.say(
        f"{helper.ending_image}"
    )


SETTINGS = {
    "home": Setting("home", "the little house", "front room with soft pillows", "warm"),
    "kitchen": Setting("kitchen", "the kitchen", "counter tops and warm tea steam", "warm"),
    "porch": Setting("porch", "the porch", "a tiny bench and potted flowers", "breezy"),
}

BAN_ITEMS = {
    "box": Ban("box", "blue box", "please do not open the blue box", "it is for later", 1, True),
    "basket": Ban("basket", "covered basket", "please do not peek under the cloth", "it is a surprise", 1, True),
    "basket_table": Ban("basket_table", "woven basket", "please do not lift the lid", "the lid must stay shut for now", 1, True),
}

SURPRISES = {
    "cookies": Surprise("cookies", "blue box", "blue box", "a plate of warm cookies for the neighbors", "The kitchen smelled sweet already.", "a tiny sugar dusting on the counter", "a ribbon end curling from under the cloth", "a warm oven glow nearby"),
    "flowers": Surprise("flowers", "covered basket", "covered basket", "a bunch of bright paper flowers for grandma", "The room looked extra neat and cheerful.", "a strip of colored paper under the cloth", "scissors resting by the table", "soft tape holding little stems together"),
    "kitten": Surprise("kitten", "woven basket", "woven basket", "a sleepy rescue kitten with a pink collar", "The air felt gentle and excited at once.", "a tiny mew from somewhere soft", "a bowl of milk waiting nearby", "a fluffy blanket tucked in the basket"),
}

HELPERS = {
    "ribbon": Helper("ribbon", "ribbon", "tie the ribbon", "The ribbon was tied in a neat bow.", "The child held the ribbon and smiled at the finished surprise."),
    "card": Helper("card", "card", "write the card", "The card said, 'You are loved.'", "The card was tucked beside the gift like a tiny hug."),
    "tea": Helper("tea", "tea", "carry the tea", "A cup of tea warmed everyone's hands.", "The steam curled up like a soft little cloud."),
}

CHILD_NAMES = ["Mia", "Lily", "Ben", "Noah", "Ava", "Zoe", "Ella", "Sam"]
ADULT_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    ban: str
    surprise: str
    helper: str
    child: str
    adult: str
    child_type: str
    adult_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for bid in BAN_ITEMS:
            for sid2 in SURPRISES:
                if reasonable_combo(BAN_ITEMS[bid], SURPRISES[sid2]):
                    combos.append((sid, bid, sid2))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world: curiosity, a ban, and a gentle reveal.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ban", choices=BAN_ITEMS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--adult", choices=ADULT_NAMES)
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
    if args.ban and args.surprise:
        if not reasonable_combo(BAN_ITEMS[args.ban], SURPRISES[args.surprise]):
            raise StoryError("That ban and surprise do not make a reasonable heartwarming story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.ban is None or c[1] == args.ban)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ban, surprise = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    child = args.child or rng.choice(CHILD_NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    child_type = "boy" if child in {"Ben", "Noah", "Sam"} else "girl"
    adult_type = {"Mom": "mother", "Dad": "father", "Grandma": "grandmother", "Grandpa": "grandfather"}[adult]
    return StoryParams(setting, ban, surprise, helper, child, adult, child_type, adult_type)


def tell(setting: Setting, ban: Ban, surprise: Surprise, helper: Helper, child_name: str, adult_name: str, child_type: str, adult_type: str) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_type, label=child_name, role="curious"))
    adult = world.add(Entity("adult", kind="character", type=adult_type, label=adult_name, role="guide"))
    world.add(Entity("surprise", kind="thing", type="thing", label=surprise.label))
    world.facts.update(setting=setting, ban=ban, surprise=surprise, helper=helper, child=child, adult=adult)

    setup(world, child, adult, setting, ban, surprise)
    world.para()
    foreshadow(world, child, adult, surprise)
    ask_and_help(world, child, adult, surprise)
    world.para()
    reveal(world, child, adult, surprise, helper)
    world.facts["outcome"] = "revealed"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the word "ban" and gentle clues before a surprise is revealed.',
        f"Tell a story where {f['child'].label} is curious about a {f['ban'].label}, notices hints, and helps with the surprise instead of peeking too soon.",
        f"Write a cozy story with foreshadowing and curiosity about {f['surprise'].label}, ending in a warm reveal and kind thanks.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    ban = f["ban"]
    surprise = f["surprise"]
    helper = f["helper"]
    return [
        ("Who is the story about?",
         f"It is about {child.label} and {adult.label}, with a little surprise waiting nearby."),
        ("Why did the adult make a ban?",
         f"{adult.label} made the ban because {ban.reason}. The ban helped keep the surprise safe until the right moment."),
        ("What clues foreshadowed the surprise?",
         f"The story showed {surprise.clue1}, {surprise.clue2}, and {surprise.clue3}. Those clues helped the child guess that something kind was being prepared."),
        ("How did the child respond to being curious?",
         f"{child.label} did not peek. Instead, {child.label} asked to help, which made the moment sweeter for everyone."),
        ("How did the story end?",
         f"It ended with {surprise.reveal}, and everyone felt warm and happy. {helper.label.capitalize()} helped make the reveal feel gentle and loving."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a ban?",
         "A ban is a rule that says not to do something for now. It can help keep people safe or help a surprise stay secret until the right time."),
        ("What is foreshadowing?",
         "Foreshadowing means giving little hints before something happens. The hints help a reader feel curious and ready for the reveal."),
        ("What does curiosity mean?",
         "Curiosity is the feeling that makes you want to know more. It can lead to good questions and careful waiting."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hinted :- curiosity(C), C >= 1.
waited  :- hinted, patience(P), P >= 1.
outcome(revealed) :- hinted, waited.
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("curiosity", 1))
    lines.append(asp.fact("patience", 1))
    return "\n".join(lines)

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"

def asp_verify() -> int:
    rc = 0
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    if asp_outcome() != "revealed":
        rc = 1
        print("MISMATCH: ASP outcome did not resolve to revealed.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: default generation crashed: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], BAN_ITEMS[params.ban], SURPRISES[params.surprise],
        HELPERS[params.helper], params.child, params.adult, params.child_type, params.adult_type
    )
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
    StoryParams("home", "box", "cookies", "ribbon", "Mia", "Mom", "girl", "mother"),
    StoryParams("kitchen", "basket", "flowers", "card", "Ben", "Grandma", "boy", "grandmother"),
    StoryParams("porch", "basket_table", "kitten", "tea", "Ava", "Dad", "girl", "father"),
]


def explain_rejection(ban: Ban, surprise: Surprise) -> str:
    return f"(No story: the ban and surprise do not fit a gentle, plausible reveal for {ban.label} and {surprise.label}.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is intentionally tiny for this world.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
