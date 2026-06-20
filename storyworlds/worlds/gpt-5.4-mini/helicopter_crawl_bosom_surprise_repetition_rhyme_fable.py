#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/helicopter_crawl_bosom_surprise_repetition_rhyme_fable.py
=========================================================================================

A standalone story world in a small fable-like domain: a child, a tiny
helicopter toy, a crawl through an under-tree den, a bosom-safe keep-it-close
comfort gesture, and a surprise that turns worry into a wiser pattern.

The world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes
- state-driven narrative beats
- reasonableness gate
- inline ASP twin
- prompts / story QA / world-knowledge QA
- generate / emit / parser / verify / JSON / trace / ASP modes

The seed asks for:
- words: helicopter, crawl, bosom
- features: Surprise, Repetition, Rhyme
- style: Fable

This script makes those words and features carry the story:
- the helicopter is a toy that can be noisy and tempting
- the crawl is a careful way to enter a small den
- bosom is used in the gentle, old-fashioned sense of holding something close
- repetition is used as a refrain
- rhyme appears in the closing moral and some repeated phrasing
- surprise is the turn: the noisy helicopter is not lost; it is found in the
  most unexpected place, and the lesson is about listening and steady care
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    mood: str
    has_den: bool = True
    den_word: str = "nest"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Toy:
    id: str
    label: str
    sound: str
    bright: str
    surprise_place: str
    noisy: bool = True
    rhymes_with: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Den:
    id: str
    label: str
    small: bool = True
    crawled_into: bool = False
    hidden_by: str = "roots"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Lesson:
    id: str
    moral: str
    rhyme_line: str
    repeat_line: str
    outcome_word: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _speak(world: World, line: str) -> None:
    world.say(line)


def _repeat_phrase(word: str, times: int = 2) -> str:
    return ", ".join([word] * times)


def _r_surprise(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    toy = world.entities.get("helicopter")
    den = world.entities.get("den")
    if not child or not toy or not den:
        return out
    if toy.meters["lost"] < THRESHOLD or not den:
        return out
    sig = ("surprise", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toy.memes["found"] += 1
    child.memes["wonder"] += 1
    den.meters["shaken"] += 1
    out.append("__surprise__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    toy = world.entities.get("helicopter")
    if not child or not parent or not toy:
        return out
    if toy.meters["found"] < THRESHOLD:
        return out
    sig = ("calm", toy.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    parent.memes["pride"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [_r_surprise, _r_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(toy: Toy, setting: Setting) -> bool:
    return toy.noisy and setting.has_den and "crawl" in setting.den_word


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, toy in TOYS.items():
            for lesson_id, lesson in LESSONS.items():
                if reasonableness_gate(toy, setting):
                    combos.append((sid, tid, lesson_id))
    return combos


def predict_loss(world: World) -> dict:
    sim = world.copy()
    sim.get("helicopter").meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("helicopter").meters["found"] >= THRESHOLD,
        "wonder": sim.get("child").memes["wonder"],
    }


def setup(world: World, child: Entity, parent: Entity, toy: Toy, den: Den) -> None:
    child.memes["joy"] += 1
    _speak(world, f"On a bright day, {child.id} and {parent.id} went by the {world.setting.place}.")
    _speak(
        world,
        f"They had a little rule they said twice and said right: "
        f"“Slow and low, slow and low.”"
    )
    _speak(
        world,
        f"The {toy.label} hummed with a soft {toy.sound}, and the old den waited "
        f"under the tree like a secret meant for a good, careful child."
    )


def tempt(world: World, child: Entity, toy: Toy, den: Den) -> None:
    child.memes["curious"] += 1
    _speak(
        world,
        f"{child.id} held the {toy.label} close to {child.pronoun('possessive')} bosom "
        f"and smiled. “I can crawl in, I can crawl in,” {child.pronoun()} said."
    )
    _speak(
        world,
        f"But the den was small, and the roots were low, and the toy was bright and bold."
    )


def warn(world: World, parent: Entity, child: Entity, toy: Toy, den: Den) -> None:
    pred = predict_loss(world)
    child.memes["pause"] += 1
    world.facts["predicted_found"] = pred["found"]
    world.facts["predicted_wonder"] = pred["wonder"]
    _speak(
        world,
        f"{parent.id} lifted a hand. “Slow and low,” {parent.pronoun()} said again. "
        f"“A toy that flies should not bump those roots, and a little crawl should stay calm.”"
    )


def act(world: World, child: Entity, toy: Toy, den: Den) -> None:
    child.memes["defiance"] += 1
    _speak(
        world,
        f"Still, {child.id} crawled in, crawled in, crawled in. "
        f"The toy gave a tiny whir-whir-whir, and then it slipped."
    )
    toy.meters["lost"] += 1
    den.crawled_into = True
    propagate(world, narrate=False)


def accident(world: World, child: Entity, toy: Toy, den: Den) -> None:
    toy.meters["lost"] += 1
    world.say(
        f"It bounced once on a root, and once on a stone, and flew out of the den "
        f"to hide somewhere unknown."
    )
    world.say(
        f"{child.id} gasped. “My helicopter! My helicopter!” {child.pronoun()} cried."
    )


def search(world: World, parent: Entity, child: Entity, toy: Toy) -> None:
    world.say(
        f"{parent.id} followed the sound, then the silence, then the smallest clue."
    )
    world.say(
        f"Under the bosom of a low branch, tucked in a nest of leaves, the lost toy was found."
    )
    toy.meters["found"] += 1
    propagate(world, narrate=False)


def lesson(world: World, parent: Entity, child: Entity, lesson: Lesson, toy: Toy) -> None:
    child.memes["wonder"] += 1
    child.memes["love"] += 1
    world.say(
        f"“A rush can rattle, but a careful crawl can recall,” {parent.id} said gently."
    )
    world.say(
        f"“When little feet move slow, little troubles go.”"
    )
    world.say(
        f"{lesson.repeat_line}. {lesson.rhyme_line}."
    )
    world.say(
        f"{parent.id} held the {toy.label} high, then placed it back in the child's hands. "
        f"The surprise was that the toy had not been lost forever; it had only been hidden by leaves."
    )
    world.say(
        f"So {child.id} smiled and said the rule one more time: “Slow and low, slow and low.”"
    )


def ending(world: World, child: Entity, parent: Entity, toy: Toy) -> None:
    child.memes["relief"] += 1
    world.say(
        f"That evening, the {toy.label} rested safely on a shelf, and {child.id} "
        f"could still see it, bright and near. The little fable ended in peace."
    )


SETTINGS = {
    "grove": Setting("grove", "the grove", "quiet", True, "nest"),
    "hill": Setting("hill", "the hill", "airy", True, "bower"),
    "orchard": Setting("orchard", "the orchard", "soft", True, "bower"),
}

TOYS = {
    "helicopter": Toy("helicopter", "helicopter", "whirr", "bright", "leafy nook", True, rhymes_with="sky"),
    "kite": Toy("kite", "kite", "flutter", "bright", "branch nook", True, rhymes_with="high"),
    "drum": Toy("drum", "drum", "tap", "loud", "stone ring", True, rhymes_with="hum"),
}

LESSONS = {
    "surprise": Lesson("surprise", "A surprise can teach a wiser step.", "What seemed lost was only hid", "Slow and low, slow and low", "surprise"),
    "repetition": Lesson("repetition", "A repeated rule can keep a child safe.", "The same small song can guide the day", "Slow and low, slow and low", "repetition"),
    "rhyme": Lesson("rhyme", "A rhyme can make a lesson stay.", "A careful heart can reach the light", "Slow and low, slow and low", "rhyme"),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Tess", "Ivy"]
BOY_NAMES = ["Otto", "Finn", "Jude", "Eli", "Pip"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    toy: str
    lesson: str
    child_name: str
    child_gender: str
    parent_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about a helicopter toy, a crawl, and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--parent")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.toy and args.lesson and not reasonableness_gate(TOYS[args.toy], SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))):
        raise StoryError("No story: the toy and setting do not make a reasonable fable here.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.toy is None or c[1] == args.toy)
              and (args.lesson is None or c[2] == args.lesson)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy, lesson = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["Aunt Wren", "Uncle Bram", "Mother Linn", "Father Reed"])
    return StoryParams(setting, toy, lesson, name, gender, parent)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity("child", kind="character", type=params.child_gender, role="seeker", label=params.child_name))
    parent = world.add(Entity("parent", kind="character", type="adult", role="guide", label=params.parent_name))
    toy = world.add(Entity("helicopter", kind="thing", type="toy", label=TOYS[params.toy].label))
    den = world.add(Entity("den", kind="place", type="den", label="the den"))
    lesson = LESSONS[params.lesson]
    setup(world, child, parent, TOYS[params.toy], Den("den", "the den"))
    world.para()
    tempt(world, child, TOYS[params.toy], Den("den", "the den"))
    warn(world, parent, child, TOYS[params.toy], Den("den", "the den"))
    act(world, child, TOYS[params.toy], Den("den", "the den"))
    world.para()
    accident(world, child, TOYS[params.toy], Den("den", "the den"))
    search(world, parent, child, toy)
    lesson(world, parent, child, lesson, toy)
    world.para()
    ending(world, child, parent, toy)
    world.facts.update(child=child, parent=parent, toy=toy, lesson=lesson, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short fable for a young child that includes the words helicopter, crawl, and bosom.",
        "Tell a gentle story where a child follows a rule, then learns a surprising lesson after a toy helicopter slips away.",
        "Write a fable with repetition and rhyme, where a parent warns a child to crawl slowly and a surprise brings the toy back."
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    toy = world.facts["toy"]
    lesson = world.facts["lesson"]
    qa = [
        QAItem(
            question="What toy is important in the story?",
            answer=f"The important toy is the {toy.label}. It is the thing the child wants to keep close and safe."
        ),
        QAItem(
            question="Why did the parent warn the child?",
            answer="The parent warned the child because the den was small and the toy could slip or bump the roots. The warning kept the story careful instead of careless."
        ),
        QAItem(
            question="What happened after the child crawled in too quickly?",
            answer="The toy slipped away and had to be found again. That surprise turned the mistake into a lesson."
        ),
        QAItem(
            question="What did the child learn at the end?",
            answer="The child learned to move slowly and listen to the repeated rule. The ending shows that calm care wins in the end."
        ),
    ]
    if world.facts["toy"].meters["found"] >= THRESHOLD:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="It ended safely, with the toy found again and placed back where it belonged. The child finished happy, wiser, and calm."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a helicopter?",
            answer="A helicopter is a flying machine with spinning blades. It can go up and down and hover in one place."
        ),
        QAItem(
            question="What does crawl mean?",
            answer="To crawl means to move on your hands and knees or close to the ground. Small children often crawl when space is tight."
        ),
        QAItem(
            question="What does bosom mean in an old story?",
            answer="In an old story, bosom means the chest or front of the body. It can mean holding something close and safe."
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that teaches a lesson. Often the lesson is simple and easy to remember."
        ),
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
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("--- world model state ---")
        for e in sample.list(world.entities.values()):
            print(e.id, e.kind, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("noisy", tid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, L) :- setting(S), toy(T), lesson(L), noisy(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        return 1
    return rc


def resolve_story_seed(args: argparse.Namespace) -> int:
    return args.seed if args.seed is not None else random.randrange(2**31)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base = resolve_story_seed(args)
    samples = []
    if args.all:
        samples = [generate(StoryParams(s, t, l, "Mina", "girl", "Mother Linn"))
                   for s, t, l in sorted(valid_combos())]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
