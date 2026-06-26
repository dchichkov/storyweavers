#!/usr/bin/env python3
"""
A standalone storyworld for a mermaid lesson-learned reconciliation tale with
magic and rhyming-story flavor.

The tiny domain:
- A young mermaid wants to use a magic conch-song.
- The magic makes glittery bubbles that drift too far.
- A friend worries, a small conflict happens, then they make peace.
- The mermaid learns to use the magic gently and share it.

The story is driven by simulated state:
- curiosity, worry, hurt, apology, forgiveness, and joy
- a physical meter for bubble-spread and glow
- a meme meter for feelings and relationship repair
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"mermaid", "girl", "woman", "mother"}
        male = {"boy", "man", "father", "triton"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the coral cove"
    afford_magic: bool = True
    rhyme_note: str = "the tide sang low and the coral glowed"


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    glow: str
    risk: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    relic: str
    name: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def rhyming_tail(a: str, b: str) -> str:
    return f"{a} and {b} made a neat little beat"


def _rule_bubble_spill(world: World) -> list[str]:
    out: list[str] = []
    mer = world.get("hero")
    if mer.meters.get("magic", 0.0) < THRESHOLD:
        return out
    if mer.meters.get("careful", 0.0) >= THRESHOLD:
        return out
    sig = ("bubble_spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mer.meters["bubble_spread"] = mer.meters.get("bubble_spread", 0.0) + 1.0
    mer.memes["worry"] = mer.memes.get("worry", 0.0) + 1.0
    out.append("The bubbles drifted wide and far, like silver seeds from a star.")
    return out


def _rule_hurt_friend(world: World) -> list[str]:
    out: list[str] = []
    mer = world.get("hero")
    friend = world.get("friend")
    if mer.meters.get("bubble_spread", 0.0) < THRESHOLD:
        return out
    sig = ("hurt_friend",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["hurt"] = friend.memes.get("hurt", 0.0) + 1.0
    friend.memes["distance"] = friend.memes.get("distance", 0.0) + 1.0
    out.append(f"{friend.label} frowned and drifted back, feeling hurt by the swirl.")
    return out


def _rule_reconcile(world: World) -> list[str]:
    out: list[str] = []
    mer = world.get("hero")
    friend = world.get("friend")
    if mer.memes.get("sorry", 0.0) < THRESHOLD:
        return out
    if friend.memes.get("hurt", 0.0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["forgive"] = friend.memes.get("forgive", 0.0) + 1.0
    friend.memes["distance"] = 0.0
    mer.memes["joy"] = mer.memes.get("joy", 0.0) + 1.0
    out.append(f"{friend.label} smiled again, and the cloudy feeling thinned.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_bubble_spill, _rule_hurt_friend, _rule_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World, use_careful: bool = False) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["magic"] = 1.0
    if use_careful:
        hero.meters["careful"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("hero").meters.get("bubble_spread", 0.0) >= THRESHOLD


SETTINGS = {
    "cove": Setting(place="the coral cove", afford_magic=True, rhyme_note="the tide sang low and the coral glowed"),
    "grotto": Setting(place="the pearl grotto", afford_magic=True, rhyme_note="the shell-light shone in a hush of foam"),
    "lagoon": Setting(place="the moonlit lagoon", afford_magic=True, rhyme_note="the water was still and the moon was bright"),
}

RELICS = {
    "conch": Relic(
        id="conch",
        label="magic conch",
        phrase="a shimmering magic conch",
        glow="glowed like a pearl at dusk",
        risk="the song could stir a stormy splash",
        lesson="use magic gently",
    ),
    "starstone": Relic(
        id="starstone",
        label="starstone charm",
        phrase="a little starstone charm",
        glow="sparkled like a sleepy star",
        risk="the sparkle could drift and distract",
        lesson="share magic kindly",
    ),
    "moonpearl": Relic(
        id="moonpearl",
        label="moon pearl",
        phrase="a moon pearl on a silver cord",
        glow="glimmered like a moonbeam",
        risk="the shine could grow too bold",
        lesson="slow magic is wise magic",
    ),
}

NAMES = ["Marina", "Nerina", "Coralie", "Luna", "Mira", "Ariel", "Nola", "Selene"]
FRIENDS = ["Tidefin", "Pebble", "Shella", "Coral", "Waver", "Dory", "Nori"]
TRAITS = ["curious", "gentle", "brave", "playful", "dreamy", "spry"]


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    relic = RELICS[params.relic]
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type="mermaid", label=params.name, traits=["little", random.choice(TRAITS)]))
    friend = world.add(Entity(id="friend", kind="character", type="fish", label=params.friend, traits=["kind"]))
    charm = world.add(Entity(id="relic", type="thing", label=relic.label, phrase=relic.phrase, owner=hero.id))

    world.say(f"{hero.label} was a little mermaid with a bright tail and a curious heart.")
    world.say(f"{hero.label} loved the {relic.label}, for it {relic.glow}.")
    world.say(f"Near {world.setting.place}, the water hummed soft; {rhyming_tail('foam', 'home')}.")

    world.para()
    world.say(f"One day, {hero.label} wanted to sing the {relic.label} awake.")
    world.say(f"That was fun and grand, but {relic.risk}.")
    world.say(f"{friend.label} warned, \"A tiny tune is best today.\"")

    hero.meters["magic"] = 1.0
    propagate(world, narrate=True)

    if world.get("hero").meters.get("bubble_spread", 0.0) >= THRESHOLD:
        world.say(f"{hero.label} gasped, for the bubbles had brushed past {friend.label}.")
        world.say(f"{friend.label} looked sad, and the sea felt less light than before.")
        friend.memes["hurt"] = 1.0

    world.para()
    world.say(f"{hero.label} bowed her head and said, \"I'm sorry for my wild, bright way.\"")
    hero.memes["sorry"] = 1.0
    hero.meters["careful"] = 1.0
    propagate(world, narrate=True)

    world.say(f"Then {hero.label} sang again, but slow and low, with {friend.label} right beside.")
    world.say(f"The magic stayed near and clear, and the coral gave back a gentle cheer.")
    world.say(f"So {hero.label} learned the day was wise: use magic with care, and peace will rise.")

    world.facts.update(
        hero=hero,
        friend=friend,
        relic=relic,
        charm=charm,
        setting=params.setting,
        reconciled=friend.memes.get("forgive", 0.0) >= THRESHOLD,
        learned=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic"]
    return [
        f'Write a rhyming story for young children about a mermaid named {hero.label} and a {relic.label}.',
        f"Tell a gentle undersea story where {hero.label} learns a lesson about magic, makes up with a friend, and ends happy.",
        f'Write a story with a mermaid, a magical object, and a reconciliation that feels like a soft rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    relic = f["relic"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who is the story about in {SETTING[setting].place}?",
            answer=f"It is about {hero.label}, a little mermaid who lives near {SETTING[setting].place}.",
        ),
        QAItem(
            question=f"What magical thing did {hero.label} want to sing awake?",
            answer=f"{hero.label} wanted to sing the {relic.label} awake, because it sparkled and felt special.",
        ),
        QAItem(
            question=f"Why did {friend.label} feel upset at first?",
            answer=f"{friend.label} felt upset because the magic made the bubbles drift too far and brush past a friend.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn in the end?",
            answer=f"{hero.label} learned to use magic gently and carefully so it could stay sweet instead of wild.",
        ),
    ]
    if f["reconciled"]:
        qa.append(
            QAItem(
                question=f"How did {hero.label} and {friend.label} make peace?",
                answer=f"{hero.label} apologized, sang more slowly, and {friend.label} forgave {hero.label} so they could smile together again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mermaid?",
            answer="A mermaid is a storybook sea person with a fish tail instead of legs.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic in stories is something strange and wonderful that can make impossible things happen.",
        ),
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to make peace again after a disagreement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    lines.append(asp.fact("feature", "lesson_learned"))
    lines.append(asp.fact("feature", "reconciliation"))
    lines.append(asp.fact("feature", "magic"))
    return "\n".join(lines)


ASP_RULES = r"""
has_feature(lesson_learned).
has_feature(reconciliation).
has_feature(magic).
valid_story(S, R) :- setting(S), relic(R), has_feature(lesson_learned), has_feature(reconciliation), has_feature(magic).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid())
    python_set = {(s, r) for s in SETTINGS for r in RELICS}
    if clingo_set == python_set:
        print(f"OK: ASP matches Python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python registries:")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection() -> str:
    return "(No story: this mermaid tale needs a setting and a magical relic.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming mermaid storyworld with magic and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
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
    if args.setting is not None and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    setting = args.setting or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    if name == friend:
        raise StoryError("The mermaid and the friend need different names.")
    return StoryParams(setting=setting, relic=relic, name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(setting="cove", relic="conch", name="Marina", friend="Tidefin"),
    StoryParams(setting="grotto", relic="starstone", name="Coralie", friend="Shella"),
    StoryParams(setting="lagoon", relic="moonpearl", name="Luna", friend="Pebble"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid story combos:")
        for s, r in combos:
            print(f"  {s} {r}")
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
            header = f"### {p.name} in {p.setting} with {p.relic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
