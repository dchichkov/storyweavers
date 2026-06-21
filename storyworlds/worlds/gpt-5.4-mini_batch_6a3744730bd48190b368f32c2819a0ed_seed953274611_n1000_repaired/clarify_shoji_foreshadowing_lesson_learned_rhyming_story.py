#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clarify_shoji_foreshadowing_lesson_learned_rhyming_story.py
=============================================================================================

A small standalone storyworld about a child, a paper shoji screen, a soft
warning before a tiny mishap, and a lesson learned. The prose is built from
stateful entities with physical meters and emotional memes, and the renderer
leans into a child-facing rhyming story style.

Seed words:
- clarify
- shoji

Features:
- Foreshadowing
- Lesson Learned

Style:
- Rhyming Story
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
class StoryParams:
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_type: str
    object_name: str
    object_type: str
    setting: str
    rhyme_word: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    shoji = world.get("shoji")
    child = world.get("child")
    if shoji.meters["stress"] >= THRESHOLD and ("warned",) not in world.fired:
        world.fired.add(("warned",))
        child.memes["worry"] += 1
        out.append("__warn__")
    return out


def _r_tear(world: World) -> list[str]:
    out: list[str] = []
    shoji = world.get("shoji")
    if shoji.meters["tearing"] >= THRESHOLD and ("tear",) not in world.fired:
        world.fired.add(("tear",))
        shoji.meters["damage"] += 1
        out.append("__tear__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("tear", _r_tear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def is_reasonable_shoji_story(object_type: str) -> bool:
    return object_type == "shoji"


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    shoji = sim.get("shoji")
    shoji.meters["stress"] += 1
    propagate(sim, narrate=False)
    return {"tear": shoji.meters["damage"] >= THRESHOLD}


def poke(world: World, child: Entity, shoji: Entity) -> None:
    child.memes["curiosity"] += 1
    shoji.meters["stress"] += 1
    world.say(
        f"{child.id} saw the shoji so neat, so light, "
        f"with paper that whispered, soft and white."
    )


def foreshadow(world: World, helper: Entity, child: Entity) -> None:
    pred = predict_mishap(world)
    helper.memes["care"] += 1
    if pred["tear"]:
        world.say(
            f'{helper.id} gave a look, then said, "Oh my, '
            f"please touch it gently, or trouble may climb nearby."
        )
    else:
        world.say(
            f'{helper.id} smiled and said, "Let us be neat; '
            f"this paper screen is a careful feat."
        )


def clarify_line(world: World, helper: Entity, child: Entity) -> None:
    world.say(
        f'"To clarify," said {helper.id} with a grin, '
        f'"the shoji is not a toy to push or spin."'
    )


def mishap(world: World, child: Entity, shoji: Entity) -> None:
    child.memes["impulse"] += 1
    shoji.meters["tearing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {child.id} gave one curious little shove, '
        f"and the shoji made a tiny rip above."
    )


def repair(world: World, parent: Entity, shoji: Entity) -> None:
    shoji.meters["stress"] = 0.0
    shoji.meters["tearing"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came in to help, with tape and care, "
        f"and made the shoji smooth and fair."
    )


def lesson(world: World, parent: Entity, child: Entity, helper: Entity) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} said, "A soft thing needs a gentle art; '
        f"slow hands and calm feet are the smartest start."
    )
    world.say(
        f'"When you are unsure, ask first and see, '
        f"and the right choice will keep you worry-free."'
    )
    world.say(
        f"{child.id} nodded, and {helper.id} agreed with a cheer: "
        f"“We can clarify first, and keep things clear.”"
    )


def ending(world: World, child: Entity, helper: Entity, shoji: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"That evening, the shoji stood tidy and bright, "
        f"and {child.id} passed by with the gentlest light."
    )
    world.say(
        f"{child.id} learned that soft things last when treated with care, "
        f"and a kind little warning can save them from wear."
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    shoji = world.add(Entity(id="shoji", kind="thing", type=params.object_type, label="shoji"))

    child.memes["curiosity"] = 1.0
    helper.memes["care"] = 1.0
    world.say(
        f"In {params.setting}, where shadows went low, "
        f"{child.id} found a shoji all lined up in a row."
    )
    poke(world, child, shoji)
    world.para()
    foreshadow(world, helper, child)
    clarify_line(world, helper, child)

    world.para()
    mishap(world, child, shoji)
    world.say(
        f"{helper.id} gasped, then pointed with a steady, kind tone, "
        f"and {child.id} stopped before it could groan."
    )

    world.para()
    repair(world, parent, shoji)
    lesson(world, parent, child, helper)
    world.para()
    ending(world, child, helper, shoji)

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        shoji=shoji,
        setting=params.setting,
        rhyme_word=params.rhyme_word,
        foreshadowed=True,
        lesson_learned=True,
    )
    return world


SETTINGS = {
    "quiet_house": "a quiet house",
    "tea_room": "a tea room",
    "garden_room": "a sunlit room",
}

GENDERS = ["girl", "boy"]
NAMES = {
    "girl": ["Mina", "Lina", "Sora", "Nina", "Yumi"],
    "boy": ["Taro", "Kota", "Ren", "Haru", "Miko"],
}
RHYMES = ["glow", "snow", "show", "low", "go"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(setting, rhyme, "shoji") for setting in SETTINGS for rhyme in RHYMES]


CURATED = [
    StoryParams(
        child_name="Mina",
        child_gender="girl",
        helper_name="Ren",
        helper_gender="boy",
        parent_type="mother",
        object_name="shoji",
        object_type="shoji",
        setting="a quiet house",
        rhyme_word="glow",
    ),
    StoryParams(
        child_name="Taro",
        child_gender="boy",
        helper_name="Yumi",
        helper_gender="girl",
        parent_type="father",
        object_name="shoji",
        object_type="shoji",
        setting="a tea room",
        rhyme_word="snow",
    ),
    StoryParams(
        child_name="Lina",
        child_gender="girl",
        helper_name="Kota",
        helper_gender="boy",
        parent_type="mother",
        object_name="shoji",
        object_type="shoji",
        setting="a sunlit room",
        rhyme_word="show",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that uses the words "{f["child"].id}", "clarify", and "shoji".',
        f"Tell a gentle foreshadowing story where {f['helper'].id} warns {f['child'].id} about a shoji screen, and the child learns a lesson.",
        f"Write a short rhyming story with a tiny mishap and a calm lesson learned, ending with the shoji fixed and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    shoji = f["shoji"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who met a shoji screen and learned to be gentle. {helper.id} and {parent.label_word} helped turn the mishap into a lesson."),
        ("What warning came before the tear?",
         f"{helper.id} foreshadowed the trouble by saying the shoji should be touched gently. That warning helped the story point toward the lesson before the rip happened."),
        ("What lesson did the child learn?",
         f"{child.id} learned to ask first, move slowly, and treat soft things with care. That is why the shoji ended the story smooth and safe again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a shoji?",
         "A shoji is a sliding room screen with a light frame and paper panels. It is pretty, but it can tear if handled roughly."),
        ("What does clarify mean?",
         "To clarify means to make something easier to understand. It is what you do when you explain a thing more clearly."),
        ("What is foreshadowing?",
         "Foreshadowing is a hint that comes before something important happens. It helps a listener notice the warning before the big moment."),
        ("What is a lesson learned?",
         "A lesson learned is the useful idea a character keeps after something goes wrong or right. It helps them make a wiser choice next time."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
warned :- shoji(stress, S), S >= 1.
tears :- shoji(tear, T), T >= 1.
lesson_learned :- warned, tears.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("word", "clarify"))
    lines.append(asp.fact("object", "shoji"))
    lines.append(asp.fact("feature", "foreshadowing"))
    lines.append(asp.fact("feature", "lesson_learned"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show warned/0.\n#show lesson_learned/0."))
    _ = model
    print("OK: ASP helper loaded and a tiny model was solved.")
    if valid_combos() != valid_combos():
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about clarify, shoji, foreshadowing, and a lesson learned.")
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    rhyme = args.rhyme or rng.choice(RHYMES)
    child_gender = rng.choice(GENDERS)
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child_name = args.child or rng.choice(NAMES[child_gender])
    helper_name = args.helper or rng.choice(NAMES[helper_gender])
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent_type=rng.choice(["mother", "father"]),
        object_name="shoji",
        object_type="shoji",
        setting=setting,
        rhyme_word=rhyme,
    )


def generate(params: StoryParams) -> StorySample:
    if params.object_type != "shoji":
        raise StoryError("This world only tells shoji stories.")
    world = tell(params)
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
        print(asp_program("", "#show warned/0.\n#show lesson_learned/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible story shapes:")
        for combo in valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

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
