#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/republican_flashback_bedtime_story.py
=====================================================================

A tiny bedtime-story world about a child, a cozy evening, and a flashback that
helps them understand a grown-up word: "republican".

The story model is intentionally small and concrete. A child gets curious at
bedtime, asks about a word heard earlier, and a grandparent answers with a calm
flashback to an old memory, turning uncertainty into comfort.

This file follows the shared Storyweavers storyworld contract:
- standalone stdlib script
- imports results eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate plus an inline ASP twin
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
        return {"grandmother": "grandma", "grandfather": "grandpa", "mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scene:
    id: str
    place: str
    cozy_detail: str
    bedtime_thing: str
    question: str
    flashback_trigger: str
    memory_place: str
    memory_object: str
    lesson: str

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
class Memory:
    id: str
    label: str
    warmth: str
    sound: str
    object_name: str

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


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["worry"] >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        world.get("room").meters["quiet"] += 1
        out.append("__quiet__")
    return out


def _r_flashback(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    if child.memes["curiosity"] >= THRESHOLD and elder.memes["memory"] >= THRESHOLD:
        sig = ("flashback",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        elder.memes["warmth"] += 1
        child.memes["comfort"] += 1
        return ["__flashback__"]
    return []


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("flashback", "memory", _r_flashback)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reasonableness_ok(scene: Scene, memory: Memory) -> bool:
    return bool(scene.question and scene.flashback_trigger and memory.label)


def child_worries_about_word(word: str) -> bool:
    return word.lower() == "republican"


def predict_calming(world: World) -> dict:
    sim = world.copy()
    _tell_flashback(sim, narrate=False)
    return {"comfort": sim.get("child").memes["comfort"], "warmth": sim.get("elder").memes["warmth"]}


def _tell_setup(world: World, scene: Scene, child: Entity, elder: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In a soft little house on a sleepy evening, {child.id} curled under a blanket "
        f"while {scene.cozy_detail}. {scene.bedtime_thing} waited nearby like a sleepy friend."
    )
    world.say(
        f'{child.id} looked up and asked, "{scene.question}"'
    )


def _tell_worry(world: World, child: Entity, word: str) -> None:
    if child_worries_about_word(word):
        child.memes["worry"] += 1
        child.memes["curiosity"] += 1
        world.say(
            f'{child.id} frowned a little. The word "{word}" sounded big and far away, '
            f"and bedtime felt a tiny bit less cozy for a moment."
        )


def _tell_flashback(world: World, elder: Entity, scene: Scene, memory: Memory) -> None:
    child = world.get("child")
    elder.memes["memory"] += 1
    predictor = predict_calming(world)
    world.facts["predicted_comfort"] = predictor["comfort"]
    world.say(
        f'{elder.label_word.capitalize()} smiled slowly, as if a door in an old hallway had opened. '
        f'"That word reminds me of when I was young," {elder.pronoun()} said, and then '
        f"{elder.pronoun()} told a little flashback."
    )
    world.say(
        f"Back then, {elder.id} had been in {memory.label}, where {memory.warmth} and {memory.sound} made the evening feel gentle."
    )
    world.say(
        f"{memory.object_name} was on the table, and somebody used the same grown-up word while talking softly about a decision."
    )
    world.say(
        f'"It meant people were choosing together," {elder.pronoun()} explained. '
        f'"No loud trouble. Just a calm kind of grown-up choice."'
    )
    child.memes["worry"] = 0.0


def _tell_resolution(world: World, child: Entity, elder: Entity, scene: Scene) -> None:
    child.memes["comfort"] += 1
    child.memes["love"] += 1
    world.say(
        f'{child.id} thought about the old memory and nodded. "{scene.lesson}" '
        f'{"That makes it sound calm," if child.memes["comfort"] >= THRESHOLD else ""} '
        f'{child.id} whispered.'
    )
    world.say(
        f'{elder.label_word.capitalize()} tucked the blanket up higher and smiled. '
        f'The room felt quiet and safe again, and {child.id} drifted toward sleep with the new word tucked neatly in mind.'
    )


def tell(scene: Scene, memory: Memory, word: str = "republican", child_name: str = "Maya",
         child_gender: str = "girl", elder_name: str = "Grandma", elder_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    room = world.add(Entity(id="room", type="room", label=scene.place))
    world.facts["word"] = word

    _tell_setup(world, scene, child, elder)
    world.para()
    _tell_worry(world, child, word)
    if child_worries_about_word(word):
        _tell_flashback(world, elder, scene, memory)
    world.para()
    _tell_resolution(world, child, elder, scene)
    world.facts.update(
        child=child,
        elder=elder,
        room=room,
        scene=scene,
        memory=memory,
        word=word,
        calm=child.memes["comfort"] >= THRESHOLD,
        flashback=True,
    )
    return world


SCENES = {
    "lamp": Scene(
        "lamp",
        "the little lamp by the bed",
        "a yellow lamp glowed like a sleepy moon",
        "a storybook with a blue cover",
        "What does republican mean?",
        "an old family photo in a wooden frame",
        "a town hall",
        "a paper star",
        "people were choosing together",
    ),
    "window": Scene(
        "window",
        "the window where the curtains drifted softly",
        "moonlight slid over the rug",
        "a stuffed rabbit with floppy ears",
        "Why did Grandpa say republican?",
        "a ribbon on a coat hook",
        "a school meeting room",
        "a folded note",
        "people were choosing together",
    ),
    "rocking": Scene(
        "rocking",
        "the rocking chair beside the bed",
        "the chair creaked a friendly little creak",
        "a glass of water on the nightstand",
        "What was republican in your story?",
        "a tiny postcard saved in a box",
        "a neighborhood room",
        "a small map",
        "people were choosing together",
    ),
}

MEMORIES = {
    "town": Memory("town", "a bright town meeting", "warm tea steamed in cups", "paper rustled softly", "a ballot box"),
    "school": Memory("school", "a schoolroom gathering", "chalk dust floated in the lamp light", "chairs scraped softly", "a chalkboard"),
    "porch": Memory("porch", "a porch talk at dusk", "fireflies blinked outside", "a screen door clicked once", "a jar of cookies"),
}

TRAITS = ["sleepy", "curious", "gentle"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    memory: str
    word: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SCENES:
        for m in MEMORIES:
            combos.append((s, m))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story for a young child that includes the word "republican" and uses a flashback.',
        f'Tell a cozy bedtime story where {f["child"].id} asks what republican means, and a grandparent answers with an old memory.',
        f'Write a gentle story in which a flashback makes the word republican feel calm and understandable before sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    scene = f["scene"]
    memory = f["memory"]
    return [
        QAItem(
            question=f"What did {child.id} ask about?",
            answer=f"{child.id} asked about the word republican. It sounded big and unfamiliar at bedtime, so {child.id} wanted a gentle explanation."
        ),
        QAItem(
            question="How did the story use a flashback?",
            answer=f"{elder.id} told a memory from long ago. In that flashback, the story moved back to {memory.label}, where {memory.warmth}."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended quietly and safely, with {child.id} feeling calm and sleepy again. The old memory helped the new word feel less scary."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly goes back to an earlier memory or time. It helps explain something happening now."
        ),
        QAItem(
            question="What is bedtime for?",
            answer="Bedtime is when children get ready to rest and sleep. Calm stories and soft lights can help the room feel peaceful."
        ),
        QAItem(
            question="Why can a gentle explanation help at bedtime?",
            answer="A gentle explanation can make a big or confusing word feel safe and familiar. That helps a child relax and drift to sleep."
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lamp", "town", "republican", "Maya", "girl", "Grandma", "grandmother", "curious"),
    StoryParams("window", "school", "republican", "Noah", "boy", "Grandpa", "grandfather", "sleepy"),
    StoryParams("rocking", "porch", "republican", "Lily", "girl", "Grandma", "grandmother", "gentle"),
]


def explain_rejection(scene: Scene, memory: Memory) -> str:
    return f"(No story: the scene {scene.id} and memory {memory.id} do not form a gentle bedtime flashback.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    lines.append(asp.fact("word", "republican"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- scene(S), memory(M), word(republican).
flashback_story :- valid(_, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, memory=None, word=None, child=None, child_gender=None, elder=None, elder_gender=None, trait=None, seed=None), random.Random(1)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with a flashback about republican.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--word", default="republican")
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.word.lower() != "republican":
        raise StoryError("This bedtime world only tells stories with the word 'republican'.")
    scene = args.scene or rng.choice(list(SCENES))
    memory = args.memory or rng.choice(list(MEMORIES))
    if (scene, memory) not in valid_combos():
        raise StoryError(explain_rejection(SCENES[scene], MEMORIES[memory]))
    trait = args.trait or rng.choice(TRAITS)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["grandmother", "grandfather"])
    child = args.child or rng.choice(["Maya", "Lily", "Noah", "Eli", "Ava", "Leo"])
    elder = args.elder or ("Grandma" if elder_gender == "grandmother" else "Grandpa")
    return StoryParams(scene, memory, args.word, child, child_gender, elder, elder_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], MEMORIES[params.memory], params.word, params.child, params.child_gender, params.elder, params.elder_gender)
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, m in asp_valid_combos():
            print(f"  {s:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
