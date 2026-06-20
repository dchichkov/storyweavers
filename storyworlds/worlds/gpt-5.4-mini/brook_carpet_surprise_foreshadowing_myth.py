#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/brook_carpet_surprise_foreshadowing_myth.py
============================================================================

A standalone story world for a tiny mythic household tale: a child notices
strange signs, an elder's hint foreshadows a hidden truth, and a surprise under
the carpet turns into a gentle ending. The words "brook" and "carpet" are part
of the story's core world, and the rendering leans mythic without becoming
formal or abstract.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import from storyworlds/results.py
- StoryParams, build_parser, resolve_params, generate, emit, main
- QAItem / StoryError / StorySample from results
- Python reasonableness gate and inline ASP twin
- --verify exercises ASP parity and a normal generation smoke test
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "seer"}
        male = {"boy", "father", "dad", "man", "king", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id



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
    mood: str
    echo: str

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
class Sign:
    id: str
    clue: str
    effect: str
    strength: int
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
class Surprise:
    id: str
    reveal: str
    gift: str
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


def _r_damp(world: World) -> list[str]:
    out: list[str] = []
    brook = world.get("brook")
    carpet = world.get("carpet")
    if brook.meters["restless"] < THRESHOLD:
        return out
    sig = ("damp",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carpet.meters["damp"] += 1
    carpet.memes["unease"] += 1
    world.get("child").memes["curiosity"] += 1
    out.append("__clue__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    carpet = world.get("carpet")
    if carpet.meters["lifted"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if world.get("brook").meters["hidden"] >= THRESHOLD:
        world.get("brook").meters["hidden"] = 0.0
        world.get("brook").meters["seen"] = 1.0
        world.get("child").memes["awe"] += 1
        out.append("__surprise__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    brook = world.get("brook")
    carpet = world.get("carpet")
    if brook.meters["seen"] < THRESHOLD:
        return out
    sig = ("settle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carpet.meters["dry"] += 1
    world.get("child").memes["calm"] += 1
    out.append("The brook sang on, and the hall grew bright again.")
    return out


CAUSAL_RULES = [
    Rule("damp", "clue", _r_damp),
    Rule("reveal", "surprise", _r_reveal),
    Rule("settle", "ending", _r_settle),
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


def predict_reveal(world: World) -> bool:
    sim = world.copy()
    sim.get("carpet").meters["lifted"] = 1
    propagate(sim, narrate=False)
    return sim.get("brook").meters["seen"] >= THRESHOLD


def valid_combo(setting: Setting, sign: Sign, surprise: Surprise) -> bool:
    return "brook" in sign.tags and "carpet" in surprise.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for gid, sign in SIGNS.items():
            for rid, surprise in SURPRISES.items():
                if valid_combo(SETTINGS[sid], sign, surprise):
                    combos.append((sid, gid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    sign: str
    surprise: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
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


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    sign = SIGNS[params.sign]
    surprise = SURPRISES[params.surprise]

    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder"))
    brook = world.add(Entity(id="brook", kind="thing", type="brook", label="the brook"))
    carpet = world.add(Entity(id="carpet", kind="thing", type="carpet", label="the carpet"))
    hall = world.add(Entity(id="hall", kind="thing", type="place", label=setting.place))

    brook.meters["hidden"] = 1.0
    brook.meters["restless"] = 1.0
    child.memes["wonder"] = 1.0
    elder.memes["knowing"] = 1.0
    world.facts["setting"] = setting
    world.facts["sign"] = sign
    world.facts["surprise"] = surprise

    world.say(
        f"In {setting.place}, {params.child} grew up hearing old songs about {setting.mood} things that waited under quiet floors."
    )
    world.say(
        f"{params.child} loved the woven {carpet.name}, yet {sign.clue}."
    )
    world.say(
        f'\"{sign.effect},\" {params.elder} said softly, as if naming a thing the stars had already written.'
    )

    world.para()
    child.memes["curiosity"] += 1
    world.say(
        f"{params.child} knelt by the {carpet.name} and listened."
    )
    world.say(
        f"From beneath it came the faint whisper of a {brook.name}, and that whisper was the first foreshadowing."
    )

    world.para()
    carpet.meters["lifted"] = 1.0
    if predict_reveal(world):
        world.say(
            f"When the {carpet.name} was lifted at last, the surprise waited beneath it."
        )
    propagate(world, narrate=True)

    world.para()
    if world.get("brook").meters["seen"] >= THRESHOLD:
        world.say(
            f"Beneath the {carpet.name} lay {surprise.reveal}. {surprise.gift}"
        )
        child.memes["joy"] += 1
        elder.memes["joy"] += 1
        world.say(
            f"{params.child} laughed, and {params.elder} nodded, because the old warning had been true."
        )
    else:
        world.say(
            f"The {carpet.name} settled back down, and the hall kept its secret."
        )

    world.facts.update(
        child=child,
        elder=elder,
        brook=brook,
        carpet=carpet,
        hall=hall,
        setting=setting,
        sign=sign,
        surprise=surprise,
        revealed=world.get("brook").meters["seen"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic little story that includes the words "brook" and "carpet" and ends with a surprise under the carpet.',
        f"Tell a child-facing myth about {f['child'].id}, an old warning, and what was hidden by the carpet in {f['setting'].place}.",
        f'Write a short story with foreshadowing and surprise where a brook is heard before it is seen.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    setting = f["setting"]
    sign = f["sign"]
    surprise = f["surprise"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {elder.id} in {setting.place}. The old place and the quiet warning make the story feel like a small myth.",
        ),
        QAItem(
            question="What clue came before the surprise?",
            answer=f"The clue was {sign.clue}. {sign.effect} was said out loud, and then the brook could be heard under the carpet.",
        ),
        QAItem(
            question="What happened when the carpet was lifted?",
            answer=f"The brook was revealed, and {surprise.reveal} was found beneath the carpet. That is the surprise the foreshadowing pointed toward.",
        ),
    ]
    if f["revealed"]:
        qa.append(
            QAItem(
                question="Why did the elder sound so sure?",
                answer=f"{elder.id} had noticed the sign early. The damp clue meant the hidden brook was already close, so the elder's warning was wise.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a brook?",
            answer="A brook is a small stream of moving water. It can whisper and sparkle, especially in a story that feels old and magical.",
        ),
        QAItem(
            question="What is a carpet?",
            answer="A carpet is a soft floor covering. In stories, it can hide things for a while and make a room feel warm or mysterious.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints at what will happen later. It helps the ending feel surprising but not random.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something that the reader does not expect right away. It often comes after little clues have been given.",
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "moonhall": Setting("moonhall", "the moon hall", "moonlit", "the stones remember"),
    "oakkeep": Setting("oakkeep", "the oak keep", "ancient", "the beams listen"),
    "riverhouse": Setting("riverhouse", "the river house", "silver", "the floor hums"),
}

SIGNS = {
    "damp_patch": Sign("damp_patch", "a damp patch darkened the corner of the room", "A brook is near", 1, tags={"brook", "clue"}),
    "cold_breeze": Sign("cold_breeze", "a cold breeze slipped across the floor", "Something hidden is awake", 1, tags={"brook", "clue"}),
    "thin_song": Sign("thin_song", "a thin song seemed to rise from under the boards", "Listen for the brook", 1, tags={"brook", "clue"}),
}

SURPRISES = {
    "moonstone": Surprise("moonstone", "a silver brook winding under the floorboards", "It carried a moonstone that gleamed like a little captured star.", tags={"brook", "carpet"}),
    "koi": Surprise("koi", "a hidden brook that threaded under the carpet", "A small golden fish flashed in the water and vanished with a wink.", tags={"brook", "carpet"}),
    "bridge": Surprise("bridge", "a bright brook-road of water under the carpet", "The carpet had covered a tiny bridge, meant for careful feet and brave hearts.", tags={"brook", "carpet"}),
}

CHILD_NAMES = ["Mira", "Eli", "Nia", "Arin", "Luna", "Soren", "Iris", "Tavi"]
ELDER_NAMES = ["Mara", "Orin", "Sel", "Aster", "Bram", "Iona"]


CURATED = [
    StoryParams("moonhall", "damp_patch", "moonstone", "Mira", "girl", "Mara", "woman"),
    StoryParams("oakkeep", "thin_song", "bridge", "Eli", "boy", "Orin", "man"),
    StoryParams("riverhouse", "cold_breeze", "koi", "Nia", "girl", "Iona", "woman"),
]


def explain_rejection(sign: Sign, surprise: Surprise) -> str:
    if "brook" not in sign.tags:
        return "(No story: the sign does not point toward a brook, so the foreshadowing would miss the ending.)"
    if "carpet" not in surprise.tags:
        return "(No story: the surprise is not hidden by the carpet, so the two seed words would not meet in one clear myth.)"
    return "(No story: this combination is not reasonable for the chosen myth.)"


def valid_sign_surprise(sign: Sign, surprise: Surprise) -> bool:
    return "brook" in sign.tags and "carpet" in surprise.tags


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, sign in SIGNS.items():
        lines.append(asp.fact("sign", gid))
        if "brook" in sign.tags:
            lines.append(asp.fact("points_to_brook", gid))
    for rid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", rid))
        if "carpet" in s.tags:
            lines.append(asp.fact("hidden_by_carpet", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, R) :- points_to_brook(S), hidden_by_carpet(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, r) for s, sign in SIGNS.items() for r, sur in SURPRISES.items() if valid_sign_surprise(sign, sur)}
    asp_set = set(asp_valid_combos())
    rc = 0
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print(" python only:", sorted(py - asp_set))
        print(" asp only:", sorted(asp_set - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic brook-and-carpet story world with foreshadowing and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.sign and args.surprise:
        if not valid_sign_surprise(SIGNS[args.sign], SURPRISES[args.surprise]):
            raise StoryError(explain_rejection(SIGNS[args.sign], SURPRISES[args.surprise]))
    combos = [(s, g, r) for s, g, r in ((s, g, r) for s in SETTINGS for g in SIGNS for r in SURPRISES)
              if (args.setting is None or s == args.setting)
              and (args.sign is None or g == args.sign)
              and (args.surprise is None or r == args.surprise)
              and valid_sign_surprise(SIGNS[g], SURPRISES[r])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sign, surprise = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(CHILD_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(setting, sign, surprise, child, child_gender, elder, elder_gender)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible sign/surprise combos:")
        for s, r in combos:
            print(f"  {s:12} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
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
