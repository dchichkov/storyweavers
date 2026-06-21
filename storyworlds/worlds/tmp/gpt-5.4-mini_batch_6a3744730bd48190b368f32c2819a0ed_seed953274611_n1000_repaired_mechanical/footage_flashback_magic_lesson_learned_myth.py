#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/footage_flashback_magic_lesson_learned_myth.py
===============================================================================

A small myth-style storyworld about a child watching old footage, stumbling into
a flashback, using magic carelessly, and learning a lesson. The simulation tracks
typed entities with physical meters and emotional memes, and the ending depends
on the world state rather than on a fixed paragraph template.

Seed words/features:
- footage
- Flashback
- Magic
- Lesson Learned
- Style: Myth
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
    title: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "goddess", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "god", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    place: str
    gives_light: bool = False
    can_show: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    safe: bool
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Lesson:
    id: str
    label: str
    phrase: str
    wisdom: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    relic = world.entities.get("relic")
    if not hero or not relic:
        return out
    if hero.meters["memory"] < THRESHOLD:
        return out
    sig = ("flashback",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["flashback_open"] = True
    hero.memes["wonder"] += 1
    if relic:
        relic.meters["glow"] += 1
    out.append("__flashback__")
    return out


def _r_magic_spill(world: World) -> list[str]:
    out: list[str] = []
    ritual = world.entities.get("ritual")
    if not ritual or ritual.meters["magic"] < THRESHOLD:
        return out
    sig = ("magic_spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("lesson").meters["needed"] += 1
    world.get("hero").memes["alarm"] += 1
    out.append("__magic__")
    return out


RULES = [Rule("flashback", "memory", _r_flashback), Rule("magic_spill", "magic", _r_magic_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rank_magic() -> list[Magic]:
    return [m for m in MAGIC.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not rank_magic():
        return combos
    for hero in HEROES:
        for artifact in ARTIFACTS:
            for magic in MAGIC.values():
                if artifact.can_show and magic.safe:
                    combos.append((hero, artifact.id, magic.id))
    return combos


def is_reasonable(artifact: Artifact, magic: Magic) -> bool:
    return artifact.can_show and magic.safe


@dataclass
class StoryParams:
    hero: str
    artifact: str
    magic: str
    lesson: str
    setting: str
    seed: Optional[int] = None
    hero_type: str = "boy"
    companion: str = "elder"
    mood: str = "curious"
    flashback_strength: int = 1
    magic_strength: int = 1
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


HEROES = {
    "ari": {"name": "Ari", "type": "boy"},
    "sera": {"name": "Sera", "type": "girl"},
    "niko": {"name": "Niko", "type": "boy"},
    "maya": {"name": "Maya", "type": "girl"},
}

ARTIFACTS = {
    "tablet": Artifact("tablet", "tablet", "a bronze tablet of old songs", "the temple wall", can_show=True, tags={"footage"}),
    "pool": Artifact("pool", "pool", "a polished basin of water", "the shrine floor", can_show=False, tags={"water"}),
    "lens": Artifact("lens", "lens", "a glass lens of remembering", "the altar stone", can_show=True, tags={"footage"}),
}

MAGIC = {
    "glimmer": Magic("glimmer", "glimmer spell", "a glimmer spell", power=2, sense=3, safe=True, tags={"magic"}),
    "flare": Magic("flare", "flare spell", "a flare spell", power=4, sense=1, safe=False, tags={"magic"}),
    "echo": Magic("echo", "echo spell", "an echo spell", power=1, sense=2, safe=True, tags={"magic"}),
}

LESSONS = {
    "patience": Lesson("patience", "lesson of patience", "the lesson of patience", "some memories should be handled gently", tags={"lesson"}),
    "care": Lesson("care", "lesson of care", "the lesson of care", "power works best when it is guided by care", tags={"lesson"}),
}

SENSE_MIN = 2

MYTHS = {
    "mountain": "the high mountain shrine",
    "river": "the river temple",
    "cave": "the moon cave",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: footage, flashback, magic, and a lesson learned.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--setting", choices=MYTHS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.artifact and args.magic:
        art = ARTIFACTS[args.artifact]
        mag = MAGIC[args.magic]
        if not is_reasonable(art, mag):
            raise StoryError("That magic cannot honestly solve the footage problem.")
    combos = [c for c in valid_combos()
              if (args.hero is None or c[0] == args.hero)
              and (args.artifact is None or c[1] == args.artifact)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hero, artifact, magic = rng.choice(sorted(combos))
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    setting = args.setting or rng.choice(sorted(MYTHS))
    return StoryParams(hero=hero, artifact=artifact, magic=magic, lesson=lesson, setting=setting)


def tell(params: StoryParams) -> World:
    world = World()
    hero_cfg = HEROES[params.hero]
    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg["type"], label=hero_cfg["name"], role="seeker", traits=["curious"]))
    elder = world.add(Entity(id="elder", kind="character", type="woman", label="the elder", role="guide"))
    artifact = world.add(Entity(id="relic", kind="thing", type="thing", label=ARTIFACTS[params.artifact].label))
    ritual = world.add(Entity(id="ritual", kind="thing", type="thing", label=MAGIC[params.magic].label))
    lesson = world.add(Entity(id="lesson", kind="thing", type="thing", label=LESSONS[params.lesson].label))

    hero.meters["memory"] = float(params.flashback_strength)
    ritual.meters["magic"] = float(params.magic_strength)

    world.say(
        f"At {MYTHS[params.setting]}, {hero_cfg['name']} stood before {artifact.label} and watched old footage flicker like a trapped star."
    )
    world.say(
        f"The images opened a flashback: a time when the same hill, the same stones, and the same wind had whispered another name."
    )
    hero.memes["longing"] += 1
    world.para()
    world.say(
        f"Wanting to mend the past, {hero_cfg['name']} lifted {ritual.phrase} and called on magic."
    )
    hero.meters["memory"] += 1
    ritual.meters["magic"] += 1
    propagate(world, narrate=False)
    if ritual.meters["magic"] >= THRESHOLD:
        world.say(
            f"The magic answered at once, bright and wild, and the footage shivered as if the old scene wanted to wake."
        )
    if magic := MAGIC[params.magic]:
        if not magic.safe:
            world.say("But the power ran hot, and it pulled the wrong memory loose.")
    world.para()
    if params.magic == "flare":
        world.say(
            f"The elder stepped in, quiet as a mountain shadow, and covered the relic before the spell could scorch it."
        )
        lesson.meters["needed"] += 1
        hero.memes["shame"] += 1
        hero.memes["humility"] += 1
    else:
        world.say(
            f"The elder watched the glow, then showed {hero_cfg['name']} how to hold the vision steady without forcing it."
        )
        hero.memes["calm"] += 1
        lesson.meters["needed"] += 1
    world.para()
    world.say(
        f"Then came the lesson learned: {LESSONS[params.lesson].wisdom}. {hero_cfg['name']} bowed, set the magic down, and let the footage rest."
    )
    hero.memes["lesson"] += 1
    hero.meters["memory"] = max(hero.meters["memory"], 1.0)
    world.facts.update(hero=hero, elder=elder, artifact=artifact, ritual=ritual, lesson=lesson, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    hero_name = HEROES[p.hero]["name"]
    return [
        f"Write a mythic story that includes the word footage and shows {hero_name} remembering the past through a flashback.",
        f"Tell a child-friendly myth where {hero_name} uses magic near old footage and learns a lesson about handling memories with care.",
        "Write a short myth with old footage, a sudden flashback, magical trouble, and a clear lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero_name = HEROES[p.hero]["name"]
    artifact = world.facts["artifact"].label
    lesson = LESSONS[p.lesson]
    qs = [
        QAItem(
            question="What did the child see at the shrine?",
            answer=f"{hero_name} saw old footage on {artifact}, and the images opened a flashback to an earlier time. The sight mattered because it pulled {hero_name} back into a memory that felt alive."
        ),
        QAItem(
            question="Why did the magic become a problem?",
            answer=f"{hero_name} used {MAGIC[p.magic].phrase} too forcefully near the footage. That made the memory glow too hard, so the elder had to step in and guide the moment back to safety."
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"{lesson.wisdom.capitalize()}. {hero_name} learned to treat old memories gently and to use power with care, not to force what should be remembered softly."
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    artifact = ARTIFACTS[p.artifact]
    mag = MAGIC[p.magic]
    lesson = LESSONS[p.lesson]
    return [
        QAItem(
            question="What is footage?",
            answer="Footage is recorded images from before, like a little moving memory that can show what happened long ago."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when the story or a person returns to an earlier moment from the past. It helps the listener feel how the old event still matters now."
        ),
        QAItem(
            question="What does magic do in a myth?",
            answer="In a myth, magic can make ordinary things feel alive, bright, or powerful. It often creates wonder, but it can also teach respect and restraint."
        ),
        QAItem(
            question="Why does a lesson matter in a myth?",
            answer="A lesson gives the story its meaning. It shows what the characters learned and how they changed after the strange event."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero="ari", artifact="tablet", magic="echo", lesson="patience", setting="mountain", hero_type="boy", companion="elder", mood="curious"),
    StoryParams(hero="sera", artifact="lens", magic="glimmer", lesson="care", setting="river", hero_type="girl", companion="elder", mood="curious"),
    StoryParams(hero="maya", artifact="tablet", magic="glimmer", lesson="care", setting="cave", hero_type="girl", companion="elder", mood="curious"),
]


def explain_rejection(artifact: Artifact, magic: Magic) -> str:
    if not artifact.can_show:
        return "(No story: that object cannot honestly carry footage, so the flashback never opens.)"
    if not magic.safe:
        return "(No story: that magic is too wild for a child-facing myth about learning care.)"
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
reasonably(Artifact, Magic) :- artifact(Artifact), magic(Magic), can_show(Artifact), safe(Magic).
valid(H, A, M) :- hero(H), artifact(A), magic(M), reasonably(A, M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        if a.can_show:
            lines.append(asp.fact("can_show", aid))
    for mid, m in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        if m.safe:
            lines.append(asp.fact("safe", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo gates differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(hero=None, artifact=None, magic=None, lesson=None, setting=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as err:
        print(f"FAIL: generation smoke test crashed: {err}")
        rc = 1
    return rc


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES or params.artifact not in ARTIFACTS or params.magic not in MAGIC or params.lesson not in LESSONS or params.setting not in MYTHS:
        raise StoryError("Invalid parameters for this storyworld.")
    return build_sample(params)


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
        for row in asp_valid_combos():
            print(row)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
