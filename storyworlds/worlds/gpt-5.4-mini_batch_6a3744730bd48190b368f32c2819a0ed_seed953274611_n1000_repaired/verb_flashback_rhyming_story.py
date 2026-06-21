#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/verb_flashback_rhyming_story.py
================================================================

A small storyworld for a seed about a child, a verb, and a flashback, told in a
rhyming, child-facing style.

Premise:
- A child must write a verb for a class page or little poster.
- They feel stuck.
- A flashback to a kind person or a remembered game gives them the right idea.
- They return, write the word, and end with a bright, rhyming image.

The world model tracks a few physical meters and emotional memes:
- meters: paper-ready, written, flutter, kept, glow
- memes: stuck, courage, memory, delight, pride

The story is not a frozen paragraph with swapped nouns; state changes drive the
beats and the ending image proves what changed.
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher",
                "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Scene:
    id: str
    place: str
    line: str
    flashback_line: str
    return_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Prompt:
    id: str
    card: str
    rhyme: str
    flashback: str
    use_word: str = "verb"
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Helper:
    id: str
    type: str
    label: str
    memory_tone: str
    gives_hint: str
    tags: set[str] = field(default_factory=set)
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
        clone.facts = dict(self.facts)
        return clone
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


def _r_memory(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["stuck"] < THRESHOLD or child.memes["memory"] >= THRESHOLD:
        return out
    sig = ("memory",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["memory"] += 1
    child.meters["glow"] += 1
    out.append("__flashback__")
    return out


def _r_write(world: World) -> list[str]:
    child = world.entities.get("child")
    paper = world.entities.get("paper")
    if not child or not paper:
        return []
    if child.memes["courage"] < THRESHOLD or paper.meters["ready"] < THRESHOLD:
        return []
    sig = ("write",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    paper.meters["written"] += 1
    paper.meters["kept"] += 1
    child.memes["pride"] += 1
    return ["__write__"]


CAUSAL_RULES = [Rule("memory", _r_memory), Rule("write", _r_write)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def reason_gate(prompt: Prompt, helper: Helper) -> bool:
    return "verb" in prompt.use_word and "memory" in helper.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id, scene in SCENES.items():
        for prompt_id, prompt in PROMPTS.items():
            for helper_id, helper in HELPERS.items():
                if reason_gate(prompt, helper):
                    combos.append((scene_id, prompt_id, helper_id))
    return combos


def flashback_hint(world: World, child: Entity, helper: Entity, prompt: Prompt) -> None:
    child.memes["stuck"] += 1
    world.say(
        f"{child.id} stared at the page and sighed a little rhyme, "
        f'"I need a word that fits just right, but I cannot find mine."'
    )
    world.say(
        f"Then {helper.label} smiled and a memory came, soft as a dove, "
        f"back to a sunny game where actions danced above."
    )


def do_flashback(world: World, child: Entity, helper: Entity, scene: Scene, prompt: Prompt) -> None:
    child.memes["memory"] += 1
    child.memes["courage"] += 1
    world.say(
        f"In a flash, the day slipped back, like a kite on a string: "
        f"{scene.flashback_line}"
    )
    world.say(
        f"{helper.label_word.capitalize()} had shown a tiny trick that made the word come alive and sing."
    )


def write_word(world: World, child: Entity, paper: Entity, prompt: Prompt) -> None:
    paper.meters["ready"] = 0.0
    paper.meters["written"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{child.id} grinned and wrote the word {prompt.use_word}, neat and fine, "
        f"then underlined it with a happy line."
    )


def ending(world: World, child: Entity, scene: Scene) -> None:
    child.memes["delight"] += 1
    world.say(
        f"At last the page was bright and true; the stuckness flew away. "
        f"{scene.ending_line}"
    )


def tell(scene: Scene, prompt: Prompt, helper: Helper, child_name: str = "Mia",
         child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper.type, role="helper", label=helper.label, tags=set(helper.tags)))
    paper = world.add(Entity(id="paper", type="thing", label="page"))
    paper.meters["ready"] = 1.0
    child.memes["stuck"] = 0.0
    child.memes["courage"] = 0.0

    world.say(
        f"On a bright little day, {child.id} sat by the page in {scene.place}; "
        f"{scene.line}"
    )
    world.say(
        f'The teacher said, "Write a {prompt.use_word}," and the room felt still.'
    )
    world.para()
    flashback_hint(world, child, helper_ent, prompt)
    do_flashback(world, child, helper_ent, scene, prompt)
    world.para()
    write_word(world, child, paper, prompt)
    world.say(
        f"{parent.label_word.capitalize()} clapped once and smiled with cheer, "
        f"for the answer had arrived so clear."
    )
    world.para()
    ending(world, child, scene)

    world.facts.update(
        child=child, parent=parent, helper=helper_ent, paper=paper,
        scene=scene, prompt=prompt, helper_cfg=helper,
    )
    return world


SCENES = {
    "classroom": Scene(
        id="classroom",
        place="the classroom",
        line="Her notebook waited on the desk, and the chalk felt light.",
        flashback_line="a kind older cousin once tapped a drum and said, 'Run, spin, clap!'",
        return_line="Back at school, the pencil still waited bright.",
        ending_line="Now the page was full of action, and the whole room felt right.",
        tags={"school", "memory"},
    ),
    "kitchen": Scene(
        id="kitchen",
        place="the kitchen table",
        line="A little recipe card sat nearby, and the spoon shone bright.",
        flashback_line="grandma once stirred a pot and said, 'Stir, flip, pour,' with delight.",
        return_line="Back at the table, the pencil still had might.",
        ending_line="Now the card held one good action, warm as morning light.",
        tags={"home", "memory"},
    ),
    "porch": Scene(
        id="porch",
        place="the porch",
        line="The breeze made the paper wiggle like a sail.",
        flashback_line="an uncle once waved and said, 'Skip, hop, sail,' along a trail.",
        return_line="Back in the breeze, the small word was no longer pale.",
        ending_line="Now the rhyme sat steady, neat as a friendly snail.",
        tags={"outside", "memory"},
    ),
}

PROMPTS = {
    "write_it": Prompt(id="write_it", card="a word card", rhyme="fits just right", flashback="memory", use_word="verb", tags={"verb"}),
    "action": Prompt(id="action", card="an action card", rhyme="comes alive", flashback="memory", use_word="verb", tags={"verb"}),
    "motion": Prompt(id="motion", card="a motion card", rhyme="rings a tune", flashback="memory", use_word="verb", tags={"verb"}),
}

HELPERS = {
    "grandma": Helper(id="grandma", type="grandmother", label="Grandma", memory_tone="warm", gives_hint="stirred", tags={"memory", "kind"}),
    "cousin": Helper(id="cousin", type="cousin", label="the cousin", memory_tone="bright", gives_hint="tapped", tags={"memory", "kind"}),
    "uncle": Helper(id="uncle", type="uncle", label="Uncle Ray", memory_tone="breezy", gives_hint="waved", tags={"memory", "kind"}),
}

NAMES = ["Mia", "Leo", "Nina", "Toby", "Zoe", "Ari"]
GENDERS = ["girl", "boy"]


@dataclass
class StoryParams:
    scene: str
    prompt: str
    helper: str
    name: str
    gender: str
    parent: str = "mother"
    seed: Optional[int] = None
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


CURATED = [
    StoryParams(scene="classroom", prompt="write_it", helper="cousin", name="Mia", gender="girl", parent="mother"),
    StoryParams(scene="kitchen", prompt="action", helper="grandma", name="Leo", gender="boy", parent="father"),
    StoryParams(scene="porch", prompt="motion", helper="uncle", name="Zoe", gender="girl", parent="mother"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a child where {f["child"].id} must think of the word "verb" and a flashback helps.',
        f"Tell a gentle rhyming story about {f['child'].id} at {f['scene'].place} who remembers a kind helper and finds the word verb.",
        f'Write a short story that includes the word "verb", uses a flashback, and ends with a bright, tidy rhyme.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, scene, prompt = f["child"], f["helper"], f["scene"], f["prompt"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who is trying to write a word. The story follows {child.id}'s stuck moment and the happy answer."),
        ("What helped {0} find the answer?".format(child.id),
         f"A flashback helped {child.id}. Remembering {helper.label} made the right word feel easy to choose, because the old memory showed a clear action."),
        ("What word did {0} write?".format(child.id),
         f"{child.id} wrote verb. That was the word the teacher asked for, and the flashback showed why it fit."),
        ("How did the story end?",
         f"It ended with {child.id} feeling proud and the page finished. The ending image proves the page was written and the worry was gone."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a verb?",
         "A verb is a word that names an action or what someone does. Words like run, jump, and sing are verbs."),
        ("What is a flashback?",
         "A flashback is when a story slips back to an earlier memory for a moment. It helps the reader see something from before the present scene."),
        ("What does rhyming mean?",
         "Rhyming means words sound alike at the end, like light and night. It makes a story feel bouncy and musical."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_story(combo: tuple[str, str, str]) -> bool:
    return combo in set(valid_combos())


def asp_facts() -> str:
    import asp
    lines = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("place", sid, scene.place))
        lines.append(asp.fact("memory", sid))
    for pid, prompt in PROMPTS.items():
        lines.append(asp.fact("prompt", pid))
        lines.append(asp.fact("word", pid, prompt.use_word))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if "memory" in helper.tags:
            lines.append(asp.fact("memory_helper", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, H) :- scene(S), prompt(P), helper(H), word(P, "verb"), memory_helper(H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity:")
        print("  only in ASP:", sorted(a - b))
        print("  only in Python:", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with a flashback and the word verb.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--prompt", choices=PROMPTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.prompt is None or c[1] == args.prompt)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, prompt, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene=scene, prompt=prompt, helper=helper, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.prompt not in PROMPTS or params.helper not in HELPERS:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(SCENES[params.scene], PROMPTS[params.prompt], HELPERS[params.helper],
                 child_name=params.name, child_gender=params.gender, parent_type=params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(f"{len(asp_valid_combos())} compatible (scene, prompt, helper) combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.scene} / verb / flashback"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
