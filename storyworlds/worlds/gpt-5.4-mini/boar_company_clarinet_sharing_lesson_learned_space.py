#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boar_company_clarinet_sharing_lesson_learned_space.py
=====================================================================================

A standalone storyworld for a small Space Adventure tale about a boar, a company,
a clarinet, sharing, and a lesson learned.

Premise:
- A tiny crew is exploring a moon base.
- One child finds a clarinet in the cargo pod.
- A boar mascot wants to join the company and hear the music.
- The clarinet must be shared carefully so everyone can enjoy it.
- A small mishap teaches a clear lesson: share the right way, and ask before
  using something delicate in space.

This file is self-contained and uses only the Python stdlib plus the shared
storyworld result containers.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    partner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    fragile: bool = False
    musical: bool = False
    boar: bool = False
    shared: bool = False

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
    scene: str
    place: str
    sky: str
    travel: str
    landing: str
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    where: str
    sound: str
    fragile: bool = False
    musical: bool = False
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
class ShareMove:
    id: str
    method: str
    safe: bool
    text: str
    fail: str
    lesson: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clarinet").meters["scratched"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["worry"] += 1
    world.get("clarinet").meters["dusty"] += 1
    out.append("__spill__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    if world.get("crew").memes["lesson"] < THRESHOLD:
        return out
    if ("lesson",) in world.fired:
        return out
    world.fired.add(("lesson",))
    out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule("spill", "physical", _r_spill),
    Rule("lesson", "social", _r_lesson),
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


SETTINGS = {
    "moonbase": Setting(
        "moonbase",
        "A silver moonbase with a round window and a humming radio.",
        "the moonbase",
        "the stars",
        "float through the moon hall",
        "touch down by the airlock",
        tags={"space", "moon"},
    ),
    "starship": Setting(
        "starship",
        "A small starship with bright panels and a cozy music nook.",
        "the starship",
        "the starlight",
        "glide through the ship",
        "dock beside the cargo bay",
        tags={"space", "ship"},
    ),
}

BOAR = {
    "boar": Entity("boar", kind="character", type="thing", label="boar", boar=True),
}

CLARINETS = {
    "clarinet": ObjectCfg(
        "clarinet",
        "clarinet",
        "a shiny clarinet",
        "the music locker",
        "toot",
        fragile=True,
        musical=True,
        tags={"music", "clarinet"},
    ),
}

SHARES = {
    "turns": ShareMove(
        "turns",
        "take turns one song at a time",
        True,
        "carefully took turns, one song at a time, so everyone could hear the music",
        "tried to take turns, but the clarinet was dropped and scratched",
        "When they took turns, everyone learned that sharing works best when the instrument is handled gently.",
        tags={"sharing"},
    ),
    "pass": ShareMove(
        "pass",
        "pass it slowly from one friend to another",
        True,
        "passed the clarinet slowly from one friend to another while the boar waited happily for its turn",
        "passed it too fast, and the clarinet bumped the rail",
        "Passing slowly taught them that sharing means being careful with what you borrow.",
        tags={"sharing"},
    ),
    "grab": ShareMove(
        "grab",
        "snatch it and play loudly",
        False,
        "snatched the clarinet and played loudly",
        "snatched the clarinet, but it slipped and made everyone gasp",
        "They learned that grabbing is not sharing, especially with something fragile.",
        tags={"sharing"},
    ),
}

NAMES = ["Mina", "Zed", "Rin", "Tao", "Luna", "Kai", "Nia", "Pip"]
PARENT_NAMES = ["captain", "engineer"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    boar_name: str
    child_name: str
    parent: str
    share_move: str
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
    for s in SETTINGS:
        for b in BOAR:
            for c in CLARINETS:
                combos.append((s, b, c))
    return combos


def _predict(world: World) -> bool:
    sim = world.copy()
    sim.get("clarinet").meters["scratched"] += 1
    propagate(sim, narrate=False)
    return sim.get("clarinet").meters["dusty"] >= THRESHOLD


def tell(setting: Setting, boar_name: str, child_name: str, parent: str, share_move: ShareMove) -> World:
    world = World()
    crew = world.add(Entity("crew", kind="character", type="thing", label="the crew", role="group"))
    boar = world.add(Entity("boar", kind="character", type="thing", label=boar_name, role="boar", boar=True))
    child = world.add(Entity("child", kind="character", type="girl", label=child_name, role="child"))
    clarinet = world.add(Entity("clarinet", type="thing", label="clarinet", fragile=True, musical=True))
    world.add(Entity("ship", type="thing", label=setting.place))

    world.say(
        f"On a bright day in {setting.place}, {child_name} and {boar_name} explored "
        f"{setting.scene.lower()}."
    )
    world.say(
        f"{child_name} found {CLARINETS['clarinet'].phrase} in {CLARINETS['clarinet'].where}, "
        f"and the little company gathered around it like a tiny band."
    )
    world.say(
        f'"We can all hear it," said {child_name}, and the boar snuffled happily because '
        f"the company felt larger with music."
    )

    world.para()
    world.say(
        f"But the clarinet was delicate, and the stars outside the window seemed to "
        f"wink while everyone thought about how to share it."
    )
    world.say(f'{child_name} wanted to {share_move.method}.')
    if _predict(world):
        world.say(f'{boar_name} looked worried, because a rough move could scratch the clarinet.')

    world.para()
    if share_move.safe:
        child.memes["care"] += 1
        boar.memes["joy"] += 1
        world.get("crew").memes["lesson"] += 1
        world.say(
            f"{child_name} slowed down, and the company {share_move.text}."
        )
        world.say(
            f"The clarinet stayed bright and smooth, and the boar got a turn too."
        )
        world.say(
            f"Then everyone smiled as the music floated through the moon hall."
        )
        world.say(
            f"At the end, the crew remembered the lesson: sharing is kinder when you "
            f"protect the things you borrow."
        )
    else:
        clarinet.meters["scratched"] += 1
        propagate(world, narrate=False)
        child.memes["lesson"] += 1
        world.say(
            f"{child_name} ignored the careful advice and {share_move.text}, which made "
            f"the clarinet bump against the rail."
        )
        world.say(
            f"The sound went squeak instead of toot, and everyone had to stop."
        )
        world.say(
            f"After that, {child_name} held the clarinet with both hands and learned that "
            f"sharing is not the same as grabbing."
        )

    world.facts.update(
        setting=setting,
        boar_name=boar_name,
        child_name=child_name,
        parent=parent,
        share_move=share_move,
        boar=boar,
        child=child,
        clarinet=clarinet,
        crew=crew,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a Space Adventure story for a 3-to-5-year-old that includes the words "boar", "company", and "clarinet".',
        f"Tell a gentle story where {f['child_name']} and a boar are traveling with a company in space and learn how to share a clarinet.",
        f"Write a child-friendly space story about sharing a clarinet, with a boar friend and a clear lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    share: ShareMove = f["share_move"]
    answers = [
        QAItem(
            question="Who was in the story?",
            answer=f"The story was about {f['child_name']}, a boar, and the company traveling together in space. The clarinet made their little crew feel like a real band.",
        ),
        QAItem(
            question="What did they find?",
            answer="They found a clarinet and wanted to hear it play. The instrument became the center of their space adventure.",
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=share.lesson,
        ),
    ]
    if share.safe:
        answers.append(
            QAItem(
                question="How did they share the clarinet?",
                answer=f"They {share.text}. That careful way kept the clarinet safe and let the boar have a turn too.",
            )
        )
        answers.append(
            QAItem(
                question="How did the story end?",
                answer="It ended happily, with music drifting through the moon hall and everyone feeling proud of their sharing.",
            )
        )
    else:
        answers.append(
            QAItem(
                question="What happened when they were not careful?",
                answer="The clarinet got scratched and the music stopped for a moment. That mistake taught them to handle shared things gently.",
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clarinet?",
            answer="A clarinet is a musical instrument with keys and a mouthpiece. It makes a clear toot when someone plays it.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something too. Good sharing also means taking care of the thing while you use it.",
        ),
        QAItem(
            question="What is a boar?",
            answer="A boar is a wild pig. In a story, a boar can be a funny or brave friend in a big adventure.",
        ),
        QAItem(
            question="What kind of place is a moonbase?",
            answer="A moonbase is a place people imagine on the Moon. It is part of a space adventure story, with stars outside and rooms inside for living and working.",
        ),
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
        if e.fragile:
            bits.append("fragile=True")
        if e.musical:
            bits.append("musical=True")
        if e.boar:
            bits.append("boar=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, B, C) :- setting(S), boar(B), clarinet(C).
safe_share(turns).
safe_share(pass).
lesson_learned(valid, turns).
lesson_learned(valid, pass).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for b in BOAR:
        lines.append(asp.fact("boar", b))
    for c in CLARINETS:
        lines.append(asp.fact("clarinet", c))
    for m in SHARES.values():
        lines.append(asp.fact("share", m.id))
        if m.safe:
            lines.append(asp.fact("safe_share", m.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print(" only in ASP:", sorted(a - p))
        print(" only in Python:", sorted(p - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("moonbase", "Boar", "Mina", "captain", "turns"),
    StoryParams("starship", "Bram", "Kai", "engineer", "pass"),
    StoryParams("moonbase", "Porkchop", "Luna", "captain", "grab"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld about a boar company, a clarinet, sharing, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--move", choices=SHARES)
    ap.add_argument("--boar-name")
    ap.add_argument("--child-name")
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid story combinations exist.)")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    move = args.move or rng.choice(sorted(SHARES))
    boar_name = args.boar_name or rng.choice(["Bram", "Bogo", "Bo", "Huff", "Snout"])
    child_name = args.child_name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(setting, boar_name, child_name, parent, move)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        params.boar_name,
        params.child_name,
        params.parent,
        SHARES[params.share_move],
    )
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t in combos:
            print("  ", t)
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
            header = f"### {p.child_name} and {p.boar_name} in {p.setting} ({p.share_move})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
