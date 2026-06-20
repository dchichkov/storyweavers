#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/duffel_foster_stand_transformation_moral_value_myth.py
======================================================================================

A small myth-styled storyworld built from the seed words **duffel**, **foster**,
and **stand**, with two core features:

* **Transformation** — something humble becomes something true and useful.
* **Moral Value** — a child learns to stand for kindness instead of fear.

This world tells close variations of one tiny mythic premise:
a child carries a duffel into a lonely place, meets a frightened being that
needs shelter, must choose whether to stand by it, and is transformed by the
choice into someone worthy of a song.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    traveler = world.entities.get("child")
    if not traveler:
        return out
    if traveler.memes["compassion"] < THRESHOLD:
        return out
    sig = ("transformed",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    traveler.meters["changed"] += 1
    traveler.memes["moral_value"] += 1
    world.get("duffel").meters["warmth"] += 1
    world.get("stone").meters["glow"] += 1
    out.append("__transformed__")
    return out


CAUSAL_RULES = [Rule("transformation", _r_transformation)]


@dataclass
class StoryParams:
    setting: str
    artifact: str
    burden: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    mystery: str
    image: str


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    warmth: str


@dataclass
class Burden:
    id: str
    label: str
    phrase: str
    need: str
    danger: str


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


SETTINGS = {
    "cairn": Setting("cairn", "the hill of old stones",
                     "On the hill of old stones, the wind sang like a flute.",
                     "At the center stood a stone circle older than any name.",
                     "The circle waited under a pale moon."),
    "river": Setting("river", "the silver riverbank",
                     "Beside the silver river, reeds bowed and whispered.",
                     "A smooth standing stone rose from the water's edge.",
                     "It shone like a wet shield in the dusk."),
    "forest": Setting("forest", "the deep forest",
                      "In the deep forest, the trees kept their ancient counsel.",
                      "A tall standing root marked a forgotten path.",
                      "Its shadow lay long across the moss."),
}

ARTIFACTS = {
    "duffel": Artifact("duffel", "duffel bag", "a worn duffel bag", "warm"),
    "cloak": Artifact("cloak", "cloak", "a little wool cloak", "soft"),
    "torch": Artifact("torch", "torch", "a small torch", "bright"),
}

BURDENS = {
    "foster": Burden("foster", "foster child", "a foster child", "needs shelter", "can be lonely"),
    "bird": Burden("bird", "stone bird", "a cracked stone bird", "needs care", "can stay broken"),
    "seed": Burden("seed", "sleeping seed", "a sleeping seed", "needs patience", "can sleep too long"),
}

RESPONSES = {
    "kindness": Response("kindness", 3, 3,
                         "gathered the little one close and gave it shelter in the moonlit path",
                         "tried to help, but the night was too cold and the moment was lost",
                         "gathered the little one close and gave it shelter"),
    "stand": Response("stand", 3, 2,
                      "stood before the cold wind and did not let it take the small life away",
                      "stood bravely, but not long enough to matter",
                      "stood before the cold wind and held the line"),
    "song": Response("song", 2, 2,
                     "sang a gentle promise and made the lonely place feel less sharp",
                     "sang, but the promise did not reach the dark",
                     "sang a gentle promise"),
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Nora", "Elin"]
BOY_NAMES = ["Arun", "Soren", "Pavel", "Ivo", "Kian"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in ARTIFACTS:
            for b in BURDENS:
                if a == "duffel" and b == "foster":
                    out.append((s, a, b))
    return out


def reasonableness_gate(artifact: Artifact, burden: Burden) -> bool:
    return artifact.id == "duffel" and burden.id == "foster"


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def outcome_of(params: StoryParams) -> str:
    return "transformed"


def _do_burden(world: World) -> None:
    world.get("child").memes["compassion"] += 1
    propagate(world, narrate=False)


def tell(setting: Setting, artifact: Artifact, burden: Burden, response: Response,
         hero: str, hero_gender: str, helper: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=hero_gender, label=hero, role="hero"))
    helper_ent = world.add(Entity("helper", kind="character", type=helper_gender, label=helper, role="helper"))
    duffel = world.add(Entity("duffel", type="thing", label=artifact.label))
    stone = world.add(Entity("stone", type="thing", label=burden.label))
    child.memes["fear"] = 0.0
    helper_ent.memes["hope"] = 1.0
    world.facts["setting"] = setting
    world.facts["artifact"] = artifact
    world.facts["burden"] = burden
    world.facts["response"] = response

    world.say(f"{setting.opening} {hero} came there with {hero.pronoun('possessive')} {artifact.label}.")
    world.say(f"Inside the {artifact.label}, {hero} carried {burden.phrase} and the quiet wish to do what was right.")
    world.para()
    world.say(f"Then {hero} saw {helper}'s need: {burden.need}, and the old stone answered with its silent {setting.mystery}.")
    world.say(f'"I will {response.id}," {hero} whispered, and {hero.pronoun()} chose to {response.id} even when the night felt stern.')
    _do_burden(world)
    world.para()
    if child.memes["compassion"] >= THRESHOLD:
        world.say(f"{hero} {response.text}.")
        world.say(f"The {artifact.label} grew warm, the standing stone gave off a soft glow, and the cold place became a place of care.")
        world.say(f"In that hour, {hero} was changed: {hero.pronoun()} learned that to stand for the small and helpless is the truest strength.")
    else:
        world.say(f"{hero} {response.fail}.")
        world.say("The myth ended in silence, and the lesson remained unlearned.")
    world.facts["hero"] = child
    world.facts["helper_ent"] = helper_ent
    world.facts["outcome"] = "transformed"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a young child that includes the words "duffel", "foster", and "stand".',
        f"Tell a gentle myth where {f['hero'].label} carries a duffel, meets something that needs fostering, and learns to stand for kindness.",
        "Write a story with a transformation and a moral lesson, ending with a child changed by a brave kind choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"].label
    setting = world.facts["setting"].place
    return [
        QAItem(
            question=f"Why did {hero} change in the story?",
            answer=f"{hero} changed because {hero} chose kindness when the small one needed care. That choice warmed the duffel and made the standing stone glow, showing the change was real."
        ),
        QAItem(
            question="What did the child learn to do?",
            answer="The child learned to stand for what was gentle and right. In the end, courage meant helping the helpless instead of turning away."
        ),
        QAItem(
            question=f"Where did the story take place?",
            answer=f"It took place at {setting}, a lonely mythic place with old stones and a serious wind. That setting made the choice feel important, as if the land itself was listening."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a duffel bag?", "A duffel bag is a soft bag used for carrying things. People can pack clothes or other small items inside it."),
        QAItem("What does it mean to foster someone?", "To foster someone means to care for them and help them grow in a safe way. It is a word about giving shelter and support."),
        QAItem("What does it mean to stand for something?", "To stand for something means to support it and not give up on it. It is a way of showing courage and moral strength."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cairn", "duffel", "foster", "kindness", "Mira", "girl", "Old Woman", "woman"),
    StoryParams("river", "duffel", "foster", "stand", "Arun", "boy", "River Keeper", "man"),
]


def explain_rejection(artifact: Artifact, burden: Burden) -> str:
    return f"(No story: this world only makes sense when a duffel can foster something small and vulnerable.)"


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ARTIFACTS:
        lines.append(asp.fact("artifact", a))
    for b in BURDENS:
        lines.append(asp.fact("burden", b))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,B) :- setting(S), artifact(A), burden(B), gate(A,B).
gate(duffel,foster).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    setting: str
    artifact: str
    burden: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of duffel, foster, and stand.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.artifact and args.burden:
        if not reasonableness_gate(ARTIFACTS[args.artifact], BURDENS[args.burden]):
            raise StoryError(explain_rejection(ARTIFACTS[args.artifact], BURDENS[args.burden]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, artifact, burden = rng.choice(combos)
    response = args.response or "kindness"
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or ("Old Woman" if helper_gender == "woman" else "Old Man")
    return StoryParams(setting, artifact, burden, response, hero, hero_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ARTIFACTS[params.artifact], BURDENS[params.burden],
                 RESPONSES[params.response], params.hero, params.hero_gender, params.helper, params.helper_gender)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combos differ.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, artifact=None, burden=None, response=None, hero=None, hero_gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
