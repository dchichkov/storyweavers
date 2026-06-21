#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/infect_legitimate_ambulance_lesson_learned_misunderstanding_happy.py
===================================================================================================

A tiny comedy storyworld about a child, a misunderstood "infect" word, a
legitimate ambulance sticker, and a happy lesson learned.

Premise
-------
A child hears a dramatic word, thinks something is wrong, and tries to "help"
by calling for an ambulance. The adult explains the misunderstanding: the word
meant a patch was "infected" in the medical sense, not that the toy itself was
infecting the whole room. The child learns when to call for real help and when
to ask questions first.

This world keeps the tone child-facing and comedic: the misunderstanding is
gentle, the adult response is calm, and the ending proves the child learned a
safer, smarter habit.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/infect_legitimate_ambulance_lesson_learned_misunderstanding_happy.py
    python storyworlds/worlds/gpt-5.4-mini/infect_legitimate_ambulance_lesson_learned_misunderstanding_happy.py --qa
    python storyworlds/worlds/gpt-5.4-mini/infect_legitimate_ambulance_lesson_learned_misunderstanding_happy.py --all
    python storyworlds/worlds/gpt-5.4-mini/infect_legitimate_ambulance_lesson_learned_misunderstanding_happy.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    risky: bool = False
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
class StoryParams:
    child_name: str
    child_gender: str
    parent_type: str
    toy: str
    misunderstanding: str
    legitimate: str
    ambulance: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


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


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def _r_panic(world: World) -> list[str]:
    out = []
    if world.get("child").meters.get("worry", 0.0) >= THRESHOLD and ("panic",) not in world.fired:
        world.fired.add(("panic",))
        world.get("child").memes["alarm"] = world.get("child").memes.get("alarm", 0.0) + 1
        out.append("__panic__")
    return out


def _r_comfort(world: World) -> list[str]:
    out = []
    if world.get("parent").meters.get("reassure", 0.0) >= THRESHOLD and ("comfort",) not in world.fired:
        world.fired.add(("comfort",))
        world.get("child").memes["relief"] = world.get("child").memes.get("relief", 0.0) + 1
        out.append("__comfort__")
    return out


CAUSAL_RULES = [Rule("panic", _r_panic), Rule("comfort", _r_comfort)]


def setup_story(world: World, child: Entity, parent: Entity, toy: Prop,
                misunderstanding: Prop, legitimate: Prop, ambulance: Prop) -> None:
    child.memes["curiosity"] = 1
    child.meters["worry"] = 0
    world.say(
        f"On a bright afternoon, {child.id} was playing with {toy.phrase}. "
        f"On the table sat {legitimate.phrase}, and {ambulance.phrase} in the toy box "
        f"looked very official."
    )
    world.say(
        f"Then {child.id} heard the word '{misunderstanding.label}' and blinked. "
        f'"Does that mean the toy can infect the whole room?" {child.id} asked, with a face '
        f'half serious and half ready to giggle.'
    )


def misunderstanding_turn(world: World, child: Entity, parent: Entity,
                          toy: Prop, misunderstanding: Prop, legitimate: Prop,
                          ambulance: Prop) -> None:
    child.meters["worry"] += 1
    world.say(
        f"{parent.label_word.capitalize()} looked up from the chair and almost laughed. "
        f'"No, no. {misunderstanding.label} means a real germ problem on a real body, '
        f'not a dramatic invisible balloon cloud."'
    )
    world.say(
        f'{child.id} squinted at {legitimate.phrase}. "So the ambulance is legitimate, '
        f'but the emergency was not?"'
    )
    world.say(
        f'{parent.label_word.capitalize()} nodded. "Exactly. The ambulance sticker is '
        f'legitimate. The worry was a misunderstanding."'
    )


def call_for_help(world: World, child: Entity, parent: Entity, ambulance: Prop) -> None:
    world.say(
        f"Still, {child.id} remembered the important part: if something truly seems wrong, "
        f"call a grown-up or an ambulance right away. So {child.id} pointed to the "
        f"{ambulance.label} and said, 'Legitimate help only!'"
    )
    parent.meters["reassure"] = parent.meters.get("reassure", 0.0) + 1
    propagate(world)


def happy_ending(world: World, child: Entity, parent: Entity, toy: Prop,
                 legitimate: Prop, ambulance: Prop) -> None:
    world.para()
    world.say(
        f"{parent.label_word.capitalize()} smiled and brought out a bandage for a tiny scraped knee "
        f"from the kitchen drawer. It was not an ambulance kind of day at all."
    )
    world.say(
        f"{child.id} grinned, tucked the {ambulance.label} back into the toy box, and "
        f"carefully placed the {toy.label} beside {legitimate.phrase}. "
        f'"I learned it," {child.id} said. "Ask first, panic never."'
    )
    world.say(
        f"And that was the end of the mix-up: no real emergency, just a funny word, "
        f"a legitimate ambulance sticker, and a child who learned a smarter way to help."
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, role="parent"))
    toy = Prop(id="toy", label="toy syringe", phrase="a toy syringe", kind="toy")
    misunderstanding = Prop(id="infect", label="infect", phrase="the word infect", kind="word")
    legitimate = Prop(id="legitimate", label="legitimate", phrase="a legitimate ambulance badge", kind="badge", risky=False)
    ambulance = Prop(id="ambulance", label="ambulance", phrase="a little ambulance toy", kind="toy", risky=False)

    setup_story(world, child, parent, toy, misunderstanding, legitimate, ambulance)
    world.para()
    misunderstanding_turn(world, child, parent, toy, misunderstanding, legitimate, ambulance)
    call_for_help(world, child, parent, ambulance)
    happy_ending(world, child, parent, toy, legitimate, ambulance)

    world.facts.update(
        child=child,
        parent=parent,
        toy=toy,
        misunderstanding=misunderstanding,
        legitimate=legitimate,
        ambulance=ambulance,
        outcome="happy",
        learned=True,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [("childroom", "infect", "ambulance")]


def explain_rejection() -> str:
    return "(No story: this world is intentionally tiny. Use the built-in infect / legitimate / ambulance setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a misunderstanding and a happy lesson learned.")
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--toy", choices=["syringe", "ambulance"])
    ap.add_argument("--n", type=int, default=1)
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
    if args.toy and args.toy not in {"syringe", "ambulance"}:
        raise StoryError(explain_rejection())
    child_gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        child_name=args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES),
        child_gender=child_gender,
        parent_type=args.parent or rng.choice(["mother", "father"]),
        toy=args.toy or "syringe",
        misunderstanding="infect",
        legitimate="legitimate",
        ambulance="ambulance",
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short comedy story for a young child that includes the words "infect", "legitimate", and "ambulance".',
        f"Tell a gentle misunderstanding story where {world.facts['child'].id} thinks the word infect is scary, but learns what it really means.",
        "Make the ending happy, with a lesson learned about asking a grown-up first.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    return [
        QAItem(question="What misunderstanding did the child have?",
               answer=f"{c.id} thought the word infect meant the toy might spread trouble all over the room. The parent explained it was really about germs and not a cartoon disaster."),
        QAItem(question="What did the child learn?",
               answer="The child learned to ask a grown-up first and to call for real help only when something truly looks unsafe. That was the lesson learned in the story."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an ambulance?",
               answer="An ambulance is a vehicle that takes sick or hurt people to get medical help fast. It is a legitimate emergency vehicle, not a toy in real life."),
        QAItem(question="What does legitimate mean?",
               answer="Legitimate means real, proper, or official. In the story, the ambulance badge was legitimate because it was the real thing."),
        QAItem(question="What does infect mean?",
               answer="Infect means to spread germs or sickness to someone or something. It is a serious word, which is why the child got confused at first."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["Prompts:"]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("Story QA:")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("World QA:")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join(
        [f"{e.id}: meters={e.meters} memes={e.memes}" for e in world.entities.values()]
    )


ASP_RULES = r"""
valid(childroom, infect, ambulance).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("room", "childroom"), asp.fact("word", "infect"), asp.fact("thing", "ambulance")])


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    derived = set(asp.atoms(model, "valid"))
    expected = set(valid_combos())
    ok = derived == expected
    print("OK: ASP matches Python." if ok else f"MISMATCH: {derived} != {expected}")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    print("OK: smoke test generated story." if sample.story else "FAIL: empty story.")
    return 0 if ok and sample.story else 1


def generate(params: StoryParams) -> StorySample:
    if params.misunderstanding != "infect" or params.legitimate != "legitimate" or params.ambulance != "ambulance":
        raise StoryError("(Invalid params: this tiny world is fixed to infect / legitimate / ambulance.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(child_name="Mia", child_gender="girl", parent_type="mother", toy="syringe", misunderstanding="infect", legitimate="legitimate", ambulance="ambulance"),
    StoryParams(child_name="Noah", child_gender="boy", parent_type="father", toy="ambulance", misunderstanding="infect", legitimate="legitimate", ambulance="ambulance"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Noah", "Max", "Sam", "Leo", "Eli"]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(show="#show valid/3."))
        print("valid combos:", asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        if i + 1 < len(samples):
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
