#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ambivalence_bellow_punk_repetition_lesson_learned_folk.py
==========================================================================================

A small folk-tale storyworld about a stubborn village bell, a punky little goose,
and a child who feels ambivalence before learning a lesson. The tale uses
repetition, a bellowing warning, and a gentle lesson-learned ending.

The world is intentionally tiny and classical:
- a child wants to do something bold,
- a helper warns them with a bellow,
- the child feels ambivalence and repeats the question,
- a wise adult or elder gives a safe alternative,
- the ending proves that the lesson stuck.

The prose should read like a folk tale, with repeated phrases and a concrete
ending image.
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
LESSON_MIN = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "elder"}
        male = {"boy", "father", "dad", "man", "elder-man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Tone:
    id: str
    place: str
    opening: str
    repeated_line: str
    closing_image: str
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


@dataclass
class Sound:
    id: str
    label: str
    phrase: str
    body: str
    warning: str
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
class Trouble:
    id: str
    label: str
    phrase: str
    risk: str
    spread: int = 1
    dangerous: bool = True
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
class SafeChoice:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_bellow(world: World) -> list[str]:
    out: list[str] = []
    bell = world.entities.get("bell")
    if bell and bell.meters["ringing"] >= THRESHOLD and ("bellow", "warned") not in world.fired:
        world.fired.add(("bellow", "warned"))
        for kid in list(world.entities.values()):
            if kid.role == "child":
                kid.memes["startle"] += 1
        out.append("__bellow__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    elder = world.entities.get("elder")
    if not child or not elder:
        return out
    if child.memes["ambivalence"] < THRESHOLD:
        return out
    if child.memes["lesson"] >= LESSON_MIN:
        return out
    if ("lesson", "learned") in world.fired:
        return out
    world.fired.add(("lesson", "learned"))
    child.memes["lesson"] += 1
    elder.memes["calm"] += 1
    out.append("__lesson__")
    return out


CAUSAL_RULES = [
    Rule("bellow", "sound", _r_bellow),
    Rule("lesson", "social", _r_lesson),
]


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


def trouble_is_real(trouble: Trouble) -> bool:
    return trouble.dangerous


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tone in TONES:
        for sound in SOUNDS:
            for trouble in TROUBLES:
                if trouble_is_real(trouble):
                    combos.append((tone, sound, trouble))
    return combos


@dataclass
class StoryParams:
    tone: str
    sound: str
    trouble: str
    child: str
    child_type: str
    elder: str
    elder_type: str
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


TONES = {
    "folk": Tone(
        id="folk",
        place="the lane by the mill",
        opening="Once, in the lane by the mill, the wind moved like an old tune.",
        repeated_line="Again and again, the child asked the same question.",
        closing_image="And the lane stayed quiet under the moon, with a safe light in the window.",
    ),
    "river": Tone(
        id="river",
        place="the bend of the river",
        opening="Once, at the bend of the river, the reeds bent low and listened.",
        repeated_line="Again and again, the child asked the same question.",
        closing_image="And the river kept its silver path while the little boat rested safely ashore.",
    ),
}

SOUNDS = {
    "bellow": Sound(
        id="bellow",
        label="bellow",
        phrase="a great bellow",
        body="bellowed so loud the hens forgot to peck",
        warning="bellowed a warning",
        tags={"bellow"},
    ),
    "bell": Sound(
        id="bell",
        label="bell",
        phrase="the village bell",
        body="rang and rang from the post",
        warning="rang out a warning",
        tags={"bellow"},
    ),
}

TROUBLES = {
    "punk_goose": Trouble(
        id="punk_goose",
        label="punk goose",
        phrase="a punk goose with a green feather",
        risk="it would nip fingers and stir trouble",
        tags={"punk"},
    ),
    "punk_fox": Trouble(
        id="punk_fox",
        label="punk fox",
        phrase="a punk fox with a torn little scarf",
        risk="it would sneak off with whatever it liked",
        tags={"punk"},
    ),
}

SAFES = {
    "song": SafeChoice(
        id="song",
        label="song",
        phrase="a soft song",
        glow="it warmed the heart",
        tags={"lesson"},
    ),
    "lantern": SafeChoice(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        glow="it glowed like honey",
        tags={"lesson"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Tess", "Mina"]
BOY_NAMES = ["Pip", "Jory", "Eli", "Finn", "Oren"]
ELDER_NAMES = ["Grandma Wren", "Old Mara", "Aunt Sol", "Old Ben"]


def explain_rejection(trouble: Trouble) -> str:
    return f"(No story: {trouble.label} must be something the child can truly learn from.)"


def reasonableness_gate(sound: Sound, trouble: Trouble) -> bool:
    return sound.label in {"bellow", "bell"} and trouble.dangerous


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TONES:
        lines.append(asp.fact("tone", tid))
    for sid in SOUNDS:
        lines.append(asp.fact("sound", sid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("dangerous", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T,S,Tr) :- tone(T), sound(S), trouble(Tr), dangerous(Tr).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combos differ.")
        rc = 1
    else:
        print(f"OK: ASP and Python agree on {len(valid_combos())} combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            tone=None, sound=None, trouble=None, child=None, child_type=None,
            elder=None, elder_type=None, seed=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld with repetition and lesson learned.")
    ap.add_argument("--tone", choices=TONES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["woman", "man"])
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
    tone = args.tone or rng.choice(list(TONES))
    sound = args.sound or rng.choice(list(SOUNDS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    if not reasonableness_gate(SOUNDS[sound], TROUBLES[trouble]):
        raise StoryError(explain_rejection(TROUBLES[trouble]))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["woman", "man"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(
        tone=tone, sound=sound, trouble=trouble,
        child=child, child_type=child_type,
        elder=elder, elder_type=elder_type,
    )


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Tone, Sound, Trouble]:
    world = World()
    tone = TONES[params.tone]
    sound = SOUNDS[params.sound]
    trouble = TROUBLES[params.trouble]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_type, role="elder"))
    bell = world.add(Entity(id="bell", kind="thing", type="thing", label="village bell"))
    child.memes["ambivalence"] = 1.0
    child.memes["curiosity"] = 1.0
    return world, child, elder, bell, tone, sound, trouble


def tell(world: World, child: Entity, elder: Entity, bell: Entity, tone: Tone, sound: Sound, trouble: Trouble) -> None:
    world.say(tone.opening)
    world.say(
        f"{child.id} met {trouble.phrase} near the road. {child.id} felt ambivalence, "
        f"for {child.pronoun()} wished to follow it and wished not to."
    )
    world.say(
        f'"Should I go?" {child.id} asked. "Should I go?" {child.id} asked again.'
    )
    world.para()
    bell.meters["ringing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {sound.phrase} {sound.body}, and {elder.id} {sound.warning}: "
        f'"Stay back, stay back. {trouble.risk}."'
    )
    world.say(
        f"{tone.repeated_line} {child.id} looked one way, then the other, and felt the wish in two halves."
    )
    world.para()
    child.memes["lesson"] += 1
    child.memes["ambivalence"] = 0.0
    world.say(
        f'"A wise child listens twice and steps once," said {elder.id}. '
        f'"A loud warning is a kind gift."'
    )
    world.say(
        f"{child.id} nodded, and this time {child.pronoun()} chose the safe path, "
        f"leaving the punk trouble to the reeds and the mud."
    )
    world.para()
    world.say(
        f"{tone.closing_image} {child.id} carried {child.pronoun('possessive')} lesson home, "
        f"and even the wind seemed to repeat it softly."
    )
    world.facts.update(
        child=child, elder=elder, bell=bell, tone=tone, sound=sound, trouble=trouble,
        lesson=True, ambivalence_start=1.0, bellowed=True
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale that includes the words "ambivalence", "bellow", and "punk".',
        f"Tell a short story for a young child where {f['child'].id} feels ambivalence, hears a bellow, and learns a lesson.",
        f"Write a repetitive folk tale with a warning, a careful choice, and a clear lesson learned at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    trouble: Trouble = f["trouble"]
    qa = [
        ("What did the child feel at first?",
         f"The child felt ambivalence at first, because {child.id} wanted to act and also wanted to stay safe. That tug-of-war made the choice hard."),
        ("What did the elder do?",
         f"{elder.id} gave a bellowing warning and told the child to stay back. The loud warning helped the child stop and think."),
        ("What did the child learn?",
         f"The child learned that a loud warning can be a gift, and that it is wise to choose the safe path. By the end, the lesson was learned and the trouble was left behind."),
    ]
    if f.get("bellowed"):
        qa.append((
            "Why was the warning repeated?",
            "It was repeated like a folk-tale refrain so the child would listen twice and remember once. Repetition made the lesson stick."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is ambivalence?",
         "Ambivalence means feeling two different ways at once. A person might want something and also be worried about it."),
        ("What does it mean to bellow?",
         "To bellow means to shout very loudly. It is the kind of sound that can carry far across a field or lane."),
        ("What does punk mean here?",
         "Here, punk means a scrappy, odd little style or creature that looks a bit wild. It gives the tale a cheeky, unruly feeling."),
        ("Why do folk tales repeat lines?",
         "Folk tales repeat lines so the listener can remember them. The repeats also make the story feel old, musical, and wise."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.tone not in TONES or params.sound not in SOUNDS or params.trouble not in TROUBLES:
        raise StoryError("Invalid story parameters.")
    world, child, elder, bell, tone, sound, trouble = _setup_world(params)
    tell(world, child, elder, bell, tone, sound, trouble)
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


CURATED = [
    StoryParams(tone="folk", sound="bellow", trouble="punk_goose", child="Mira", child_type="girl", elder="Old Mara", elder_type="woman"),
    StoryParams(tone="river", sound="bell", trouble="punk_fox", child="Pip", child_type="boy", elder="Grandma Wren", elder_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t, s, tr in combos:
            print(f"  {t:8} {s:8} {tr}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
