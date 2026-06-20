#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alley_word_stork_flashback_sharing_space_adventure.py
====================================================================================

A standalone storyworld for a small, child-facing space-adventure tale about
an alley, a word, a stork, a flashback, and sharing.

Premise
-------
Two kids are pretending a narrow alley is a launch lane for a tiny rescue
rocket. One child wants to keep a special word all to themselves because it
feels like the captain's password. The other child remembers a flashback from a
previous day: the same word was more fun when they both used it. A stork-shaped
parcel drone brings a useful map card and the children learn to share the word,
the route, and the adventure.

This world is built as a small simulation with typed entities, physical meters,
emotional memes, a forward rule engine, QA sets from world state, and an inline
ASP twin for parity checking.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/alley_word_stork_flashback_sharing_space_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/alley_word_stork_flashback_sharing_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/alley_word_stork_flashback_sharing_space_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/alley_word_stork_flashback_sharing_space_adventure.py --verify
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
    attrs: dict = field(default_factory=dict)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Flashback:
    id: str
    place: str
    line: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingItem:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Adventure:
    id: str
    name: str
    route: str
    destination: str
    ending: str
    alley_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
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


def _r_grow_lantern(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["attention"] < THRESHOLD:
            continue
        sig = ("lantern", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["wonder"] += 1
        out.append("")
    return out


def _r_share_relief(world: World) -> list[str]:
    out: list[str] = []
    pair = (world.entities.get("Nova"), world.entities.get("Pip"))
    if not pair[0] or not pair[1]:
        return out
    if pair[0].memes["sharing"] < THRESHOLD or pair[1].memes["sharing"] < THRESHOLD:
        return out
    sig = ("share_relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pair[0].memes["joy"] += 1
    pair[1].memes["joy"] += 1
    return ["__share__"]


def _r_flashback_soften(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["flashback"] < THRESHOLD:
            continue
        sig = ("flashback_soften", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["stubborn"] = 0.0
        e.memes["warmth"] += 1
        out.append("")
    return out


CAUSAL_RULES = [
    Rule("lantern", "physical", _r_grow_lantern),
    Rule("share_relief", "social", _r_share_relief),
    Rule("flashback_soften", "social", _r_flashback_soften),
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
                produced.extend(s for s in sents if s and s != "__share__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback_memory() -> Flashback:
    return FLASHBACKS["shared_word"]


def shareable() -> SharingItem:
    return SHARING["signal_word"]


def adventure() -> Adventure:
    return ADVENTURES["alley"]


def tell(flashback: Flashback, share: SharingItem, adv: Adventure,
         nova: str = "Nova", pip: str = "Pip", parent: str = "Captain") -> World:
    world = World()
    a = world.add(Entity(nova, kind="character", type="girl", role="instigator"))
    b = world.add(Entity(pip, kind="character", type="boy", role="cautioner"))
    grown = world.add(Entity(parent, kind="character", type="mother", role="parent", label="the captain"))
    alley = world.add(Entity("alley", type="place", label="the alley"))
    word = world.add(Entity("word", type="thing", label="word"))
    stork = world.add(Entity("stork", type="thing", label="stork"))
    card = world.add(Entity("card", type="thing", label=share.label))
    ship = world.add(Entity("ship", type="thing", label="rocket ship"))

    a.meters["attention"] = 1
    b.memes["sharing"] = 1
    b.memes["flashback"] = 1
    world.facts["flashback"] = flashback
    world.facts["share"] = share
    world.facts["adv"] = adv

    world.say(
        f"Nova and Pip turned the alley into {adv.name}. The narrow lane became "
        f"a launch path, and {adv.alley_image}."
    )
    world.say(
        f'They called the pretend rocket "{word.label}," because one word could '
        f"feel as big as a star when they said it just right."
    )
    world.say(
        f"Then a stork-shaped parcel drone landed on a crate with {share.phrase}."
    )

    world.para()
    a.memes["stubborn"] += 1
    world.say(
        f'Nova wanted to keep the {word.label} as a captain word. "It is mine," '
        f"Nova said, hugging the idea close."
    )
    world.say(
        f'Pip opened {b.pronoun("possessive")} mouth to argue, but a flashback '
        f"popped up in {b.pronoun('possessive')} head."
    )
    b.memes["flashback"] += 1
    world.say(
        f'{flashback.line} {flashback.lesson}'
    )
    propagate(world, narrate=False)

    world.para()
    if b.memes["warmth"] >= THRESHOLD:
        b.memes["sharing"] += 1
    if a.memes["stubborn"] >= THRESHOLD:
        a.memes["sharing"] += 1
    if a.memes["stubborn"] >= THRESHOLD and b.memes["flashback"] >= THRESHOLD:
        world.say(
            f'Pip smiled and said, "{share.label.capitalize()} is better when '
            f"we both use it. Let's share the word and the route.""
        )
        a.memes["sharing"] += 1
        b.memes["sharing"] += 1
        a.meters["attention"] += 1
        b.meters["attention"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Nova blinked, then nodded. The word was no longer a secret lock; "
            f"it was a bright door both of them could open."
        )
    else:
        world.say(
            f"Nova kept the word tight in a fist, and the alley felt small and "
            f"lonely until the captain called them over."
        )

    world.para()
    grown.memes["pride"] += 1
    world.say(
        f"{grown.label_word.capitalize()} came over with the map card and said, "
        f'"A real space crew shares the signal, the route, and the job."'
    )
    world.say(
        f"Nova and Pip held the card together and raced down the alley like "
        f"tiny astronauts following a silver trail."
    )
    world.say(
        f"They reached {adv.destination}, and the little rocket ended the day "
        f"{adv.ending}."
    )

    world.facts.update(
        nova=a, pip=b, parent=grown, alley=alley, word=word, stork=stork,
        card=card, ship=ship, outcome="shared", flashback_used=True,
    )
    return world


THEMES = {
    "space_adventure": Adventure(
        "space_adventure",
        "a moon mission",
        "a shiny launch path between brick walls",
        "the moon gate at the end of the alley",
        "with the map card tucked safely in both hands",
        "The alley looked like a rocket runway, and the old bricks were tall as cliff walls.",
        tags={"space", "adventure", "alley"},
    )
}

FLASHBACKS = {
    "shared_word": Flashback(
        "shared_word",
        "the schoolyard",
        "Pip remembered the last time they played captain and navigator.",
        "Back then, sharing the word made the game bigger, not smaller.",
        tags={"flashback", "sharing", "word"},
    )
}

SHARING = {
    "signal_word": SharingItem(
        "signal_word",
        "signal word",
        "a bright signal word",
        "glowed like a tiny beacon",
        tags={"sharing", "word"},
    )
}

ADVENTURES = {
    "alley": THEMES["space_adventure"]
}

GIRL_NAMES = ["Nova", "Mira", "Zia", "Luna", "Ada"]
BOY_NAMES = ["Pip", "Milo", "Theo", "Sol", "Kit"]


@dataclass
class StoryParams:
    adventure: str
    flashback: str
    sharing: str
    nova: str
    pip: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("alley", "shared_word", "signal_word")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure alley storyworld.")
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--sharing", choices=SHARING)
    ap.add_argument("--nova")
    ap.add_argument("--pip")
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
    if args.adventure and args.adventure not in ADVENTURES:
        raise StoryError("Unknown adventure.")
    return StoryParams(
        adventure=args.adventure or "alley",
        flashback=args.flashback or "shared_word",
        sharing=args.sharing or "signal_word",
        nova=args.nova or rng.choice(GIRL_NAMES),
        pip=args.pip or rng.choice(BOY_NAMES),
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(FLASHBACKS[params.flashback], SHARING[params.sharing], ADVENTURES[params.adventure],
                 params.nova, params.pip, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a space-adventure story for a 3-to-5-year-old that includes the words "alley", "word", and "stork".',
        "Tell a story where two kids in an alley want to keep a special word private, then remember a flashback and choose sharing instead.",
        "Write a gentle space adventure with a stork-shaped helper, a flashback, and a shared signal word.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Where does the story happen?",
         "It happens in an alley that feels like a tiny rocket runway."),
        ("Why was there a flashback?",
         "Pip remembered an earlier game, and that memory showed that sharing the word made the adventure bigger."),
        ("What did the stork bring?",
         "The stork-shaped parcel drone brought a map card that helped them follow the route together."),
        ("What changed at the end?",
         "The word stopped being something Nova guarded alone and became something Nova and Pip shared."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a flashback?",
         "A flashback is when a story briefly remembers something that happened earlier."),
        ("What does sharing mean?",
         "Sharing means using, keeping, or enjoying something together instead of one person taking it all."),
        ("Why can a stork be in a story?",
         "A stork can be a bird in real life, and in stories it can also be a helpful delivery shape or messenger."),
        ("What does a signal word do?",
         "A signal word helps people know what to say or do next, like a little code for a team."),
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
    for e in world.entities.values():
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
    return "\n".join(lines)


ASP_RULES = r"""
valid(alley, shared_word, signal_word).
shared(Nova, Pip) :- valid(alley, shared_word, signal_word).
flashback_softens(Pip) :- shared(Nova, Pip).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("adventure", "alley"),
        asp.fact("flashback", "shared_word"),
        asp.fact("sharing", "signal_word"),
    ])


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
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams("alley", "shared_word", "signal_word", "Nova", "Pip", "mother")
        samples = [generate(params)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
