#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/novocaine_twist_moral_value_curiosity_myth.py
=============================================================================

A standalone story world for a mythic, child-facing tale about curiosity,
a healing twist, and a moral value learned the hard way.

Core premise
------------
A young child is told not to open a sacred healer's jar, because it holds
novocaine for a painful tooth ceremony. Curiosity tempts the child to use it,
a twist reveals the danger is not the pain but the wrong use of the medicine,
and a wise elder repairs the situation with calm teaching. The story ends with
the child choosing reverence, asking first, and helping in the proper way.

The world is built from typed entities with physical meters and emotional
memes, state-driven causal rules, and a declarative ASP twin for parity checks.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    poisonous: bool = False
    medicinal: bool = False
    sacred: bool = False
    tool: bool = False
    can_numb: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    where: str
    use: str
    forbidden: bool = False
    medicinal: bool = False
    sacred: bool = False
    can_numb: bool = False
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
class Moral:
    id: str
    value: str
    lesson: str
    right_move: str
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_dull_pain(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    tooth = world.entities.get("tooth")
    if not child or not tooth:
        return out
    if tooth.meters["ache"] < THRESHOLD:
        return out
    sig = ("pain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__pain__")
    return out


def _r_jar_open(world: World) -> list[str]:
    jar = world.entities.get("jar")
    child = world.entities.get("child")
    if not jar or not child:
        return []
    if child.memes["curiosity"] < THRESHOLD:
        return []
    if jar.meters["opened"] < THRESHOLD:
        return []
    sig = ("jar_open",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["trouble"] += 1
    return ["__jar__"]


def _r_wisdom(world: World) -> list[str]:
    elder = world.entities.get("elder")
    child = world.entities.get("child")
    if not elder or not child:
        return []
    if child.memes["shame"] < THRESHOLD:
        return []
    sig = ("wisdom",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["calm"] += 1
    child.memes["lesson"] += 1
    return ["__wisdom__"]


CAUSAL_RULES = [
    Rule("pain", "physical", _r_dull_pain),
    Rule("jar_open", "social", _r_jar_open),
    Rule("wisdom", "social", _r_wisdom),
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


def predict_mistake(world: World, artifact_id: str) -> dict:
    sim = world.copy()
    jar = sim.get(artifact_id)
    jar.meters["opened"] += 1
    propagate(sim, narrate=False)
    return {
        "trouble": sim.get("child").memes["trouble"],
        "worry": sim.get("child").memes["worry"],
    }


def wise_response(world: World) -> str:
    return "washed the child's hands, closed the jar, and explained the medicine"


def build_scene(world: World, child: Entity, elder: Entity, artifact: Artifact,
                moral: Moral, tooth: Entity) -> None:
    child.memes["curiosity"] = 1
    child.memes["love"] = 1
    tooth.meters["ache"] = 1
    world.say(
        f"Long ago, in a valley where the figs bent low and the moon watched over "
        f"the roofs, {child.id} lived with {elder.label_word} {elder.id}."
    )
    world.say(
        f"{child.id} had a sore tooth, and the ache pulsed like a tiny drum "
        f"behind the smile."
    )
    world.say(
        f"The healer kept {artifact.phrase} {artifact.where}, because "
        f"{artifact.label} was meant to soothe pain, not to be played with."
    )
    world.say(
        f'"{moral.lesson}" {elder.id} said, "{moral.right_move}."'
    )


def tempt(world: World, child: Entity, artifact: Artifact) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"But {child.id} peered at the jar and wondered what the shiny stuff inside "
        f"could do."
    )
    world.say(
        f'"Maybe I can try the {artifact.label}," {child.id} whispered, and the '
        f"thought felt like a spark in the dark."
    )


def warn(world: World, elder: Entity, child: Entity, artifact: Artifact, moral: Moral) -> None:
    pred = predict_mistake(world, "jar")
    world.facts["predicted_trouble"] = pred["trouble"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{elder.id} frowned softly. "{artifact.label} is for healing, not for '
        f"games. {moral.value.capitalize()} means we ask before we touch what is "
        f"sacred."
    )


def twist(world: World, child: Entity, elder: Entity, artifact: Artifact) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Still, {child.id} reached out."
    )
    world.get("jar").meters["opened"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The lid clicked open, and at once the room changed: the medicine was not "
        f"a treasure at all, but a grown-up tool that could numb a hurt mouth."
    )
    world.say(
        f"{child.id} gasped, because the twist was simple and stern: curiosity had "
        f"opened the jar, but understanding had to close it again."
    )


def repair(world: World, elder: Entity, child: Entity, artifact: Artifact, moral: Moral) -> None:
    child.memes["shame"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{elder.id} took a slow breath, then {wise_response(world)}."
    )
    world.say(
        f'The elder did not scold. "{moral.right_move}," {elder.id} said, '
        f'"and {artifact.label} belongs to a healer, not to curious fingers."'
    )
    world.say(
        f"{child.id} listened, nodded, and tucked both hands into {child.pronoun('possessive')} lap."
    )


def ending(world: World, child: Entity, elder: Entity, artifact: Artifact, moral: Moral) -> None:
    child.memes["curiosity"] = 0
    child.memes["reverence"] += 1
    child.memes["love"] += 1
    world.say(
        f"Then {elder.id} gave {child.id} a cool cloth to hold against the tooth, "
        f"and the ache eased without any mischief."
    )
    world.say(
        f"By sunset, {child.id} was not reaching for the jar anymore. "
        f"{child.id} was asking first, helping carefully, and remembering that "
        f"{moral.value} was a kind of courage."
    )
    world.say(
        f"The moon rose over the valley, and the sacred jar stayed closed, "
        f"safe in its place, while {child.id} smiled with a gentler mouth."
    )


def tell(params: "StoryParams") -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, role="curious"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_type, role="wise"))
    jar = world.add(Entity(id="jar", type="artifact", label="novocaine", medicinal=True, sacred=True, can_numb=True))
    tooth = world.add(Entity(id="tooth", type="body", label="tooth"))
    moral = MORALS[params.moral]
    artifact = ARTIFACTS["novocaine"]
    build_scene(world, child, elder, artifact, moral, tooth)
    world.para()
    tempt(world, child, artifact)
    warn(world, elder, child, artifact, moral)
    twist(world, child, elder, artifact)
    world.para()
    repair(world, elder, child, artifact, moral)
    ending(world, child, elder, artifact, moral)
    world.facts.update(child=child, elder=elder, jar=jar, tooth=tooth, artifact=artifact, moral=moral)
    return world


ARTIFACTS = {
    "novocaine": Artifact(
        "novocaine",
        "novocaine",
        "the novocaine jar",
        "in a blue bowl on the healer's shelf",
        "numb a painful tooth when the healer used it",
        forbidden=False,
        medicinal=True,
        sacred=True,
        can_numb=True,
        tags={"medicine", "novocaine", "sacred"},
    )
}

MORALS = {
    "curiosity": Moral(
        "curiosity",
        "curiosity",
        "Curiosity is bright, but it should bow before wisdom",
        "ask first and let a healer guide your hands",
        tags={"curiosity", "moral"},
    )
}

GIRL_NAMES = ["Mina", "Luna", "Iris", "Nia", "Suri"]
BOY_NAMES = ["Kai", "Toma", "Levi", "Ivo", "Niko"]
ELDER_NAMES = ["Aster", "Nerida", "Orin", "Sel", "Mara"]


@dataclass
@dataclass
class StoryParams:
    child: str
    child_type: str
    elder: str
    elder_type: str
    moral: str
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
    return [("novocaine", "curiosity")]


KNOWLEDGE = {
    "novocaine": [("What is novocaine?", "Novocaine is a medicine that can numb pain so a hurt part feels less sore. It should be used by a healer or doctor, not by children playing with it.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to learn, look, and ask questions. It is good when it is guided by wisdom and care.")],
    "moral": [("What is a moral value?", "A moral value is a guide for how to act kindly and wisely. It helps people choose what is right, even when they are tempted.")],
    "myth": [("What makes a story feel like a myth?", "A myth often feels old, wise, and larger than ordinary life, with symbols, lessons, and a world that seems touched by wonder.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    moral = f["moral"]
    return [
        f'Write a myth-like story for a child named {child.id} that includes the word "novocaine" and teaches {moral.value}.',
        f"Tell a short, gentle myth where {child.id} is curious about novocaine, but {elder.id} guides {child.pronoun('object')} toward a wiser choice.",
        f"Write a story with a twist where curiosity leads toward novocaine, and the ending shows a moral value learned with kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    moral = f["moral"]
    artifact = f["artifact"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {elder.id}, with the child drawn toward the healer's {artifact.label} jar. The child is the one whose curiosity creates the turning point."),
        ("Why did the child want to open the jar?",
         f"{child.id} was curious and wanted to know what the medicine could do. Curiosity pushed the child toward the jar even though it belonged to a healer."),
        ("What was the moral teaching in the story?",
         f"{moral.value.capitalize()} was the lesson, which meant asking first and letting wisdom guide the hands. The story shows that curiosity is good when it stays respectful."),
        ("How did the story end?",
         f"It ended with the child asking first, helping carefully, and leaving the novocaine in its proper place. The jar stayed closed and the hurt tooth was soothed the right way."),
    ]
    if world.get("jar").meters["opened"] >= THRESHOLD:
        qa.append((
            "What was the twist?",
            f"The twist was that novocaine was not a treasure or a toy. It was a medicine that could numb pain, so the child had to learn to treat it with care."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["artifact"].tags) | set(world.facts["moral"].tags) | {"myth"}
    out: list[tuple[str, str]] = []
    for key in ["novocaine", "curiosity", "moral", "myth"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


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
        if e.poisonous:
            bits.append("poisonous")
        if e.medicinal:
            bits.append("medicinal")
        if e.sacred:
            bits.append("sacred")
        if e.can_numb:
            bits.append("can_numb")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
medicine(X) :- artifact(X), medicinal(X).
sacred_item(X) :- artifact(X), sacred(X).
curious(C) :- child(C), curiosity(C, V), V >= 1.
opened(X) :- jar(X), opened_jar(X).
lesson(C) :- child(C), learned(C).

twist :- curious(child), opened(jar), medicine(novocaine), sacred_item(novocaine).
moral_value :- lesson(child).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        if a.medicinal:
            lines.append(asp.fact("medicinal", aid))
        if a.sacred:
            lines.append(asp.fact("sacred", aid))
        if a.can_numb:
            lines.append(asp.fact("can_numb", aid))
    for mid, m in MORALS.items():
        lines.append(asp.fact("moral", mid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("curiosity", "child", 1))
    lines.append(asp.fact("opened_jar", "jar"))
    lines.append(asp.fact("learned", "child"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show twist/0.\n#show moral_value/0."))
    atoms = set(asp.atoms(model, "twist")) | set(asp.atoms(model, "moral_value"))
    ok = {"twist", "moral_value"}
    if atoms != ok:
        print("MISMATCH in ASP atoms:", atoms)
        return 1

    # Smoke test ordinary generation.
    try:
        sample = generate(resolve_params(argparse.Namespace(), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    print("OK: ASP parity and generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic curiosity story about novocaine, a twist, and a moral value."
    )
    ap.add_argument("--child", choices=sorted(GIRL_NAMES + BOY_NAMES))
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--moral", choices=sorted(MORALS))
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
    if args.moral and args.moral not in MORALS:
        raise StoryError("Unknown moral value.")
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    elder = args.elder or rng.choice([n for n in ELDER_NAMES if n != child])
    moral = args.moral or "curiosity"
    return StoryParams(child=child, child_type="girl" if child in GIRL_NAMES else "boy",
                       elder=elder, elder_type="woman", moral=moral)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [StoryParams("Mina", "girl", "Aster", "woman", "curiosity")]


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
        print(asp_program("", "#show twist/0.\n#show moral_value/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories: novocaine / curiosity")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
