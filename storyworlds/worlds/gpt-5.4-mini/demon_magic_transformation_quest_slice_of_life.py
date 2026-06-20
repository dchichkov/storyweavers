#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/demon_magic_transformation_quest_slice_of_life.py
=================================================================================

A small story world for a slice-of-life tale about a gentle demon, a little bit
of magic, a transformation, and a neighborhood quest.

Premise:
- A child and a friendly demon live near each other.
- A magic mishap changes the demon's form.
- They go on a tiny quest through ordinary places to gather what they need.
- The ending proves the change: the demon is transformed back, and the day feels
  calmer, warmer, and more ordinary again.

The world is deliberately small and constraint-driven: only a few sensible
scenario combinations are allowed, and invalid choices raise StoryError with a
clear reason.
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
MAGIC_SAFE_MIN = 2


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
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class DemonForm:
    id: str
    label: str
    small_label: str
    clue: str
    needs: str
    comfort_phrase: str
    stubbornness: int = 0

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
class QuestStep:
    id: str
    place: str
    item: str
    phrase: str
    help_text: str
    magic_cost: int = 1

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
class Spell:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_magic_tire(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["magic"] < THRESHOLD:
            continue
        sig = ("tire", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["tired"] += 1
        out.append("")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    demon = world.entities.get("demon")
    if not demon:
        return out
    if demon.meters["transformed"] < THRESHOLD:
        return out
    sig = ("transform", demon.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    demon.memes["surprise"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("magic_tire", "social", _r_magic_tire), Rule("transformation", "magic", _r_transformation)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(form: DemonForm, quest: list[QuestStep], spell: Spell) -> bool:
    return spell.sense >= MAGIC_SAFE_MIN and bool(quest) and form.needs in {q.item for q in quest}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for form_id in FORMS:
        for quest_id, steps in QUESTS.items():
            for spell_id, spell in SPELLS.items():
                if reasonableness_gate(FORMS[form_id], steps, spell):
                    combos.append((form_id, quest_id, spell_id))
    return combos


def make_tap(world: World, child: Entity, demon: Entity, form: DemonForm) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"After breakfast, {child.id} found a friendly demon named {demon.id} "
        f"by the apartment stairs. {demon.id} was small enough to fit on the bottom step, "
        f"and {demon.pronoun().capitalize()} looked embarrassed about {form.clue}."
    )
    world.say(
        f'"I think {demon.id} needs a little magic," {child.id} said, '
        f'clutching a list for a tiny quest.'
    )


def trigger_spell(world: World, demon: Entity, spell: Spell) -> None:
    demon.meters["magic"] += 1
    demon.meters["transformed"] += 1
    demon.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the kitchen table, {demon.id} touched the spell and a warm glow went "
        f"round and round the room. {spell.text}."
    )


def quest_step(world: World, child: Entity, demon: Entity, step: QuestStep) -> None:
    world.say(
        f"First they walked to {step.place}. {child.id} asked nicely, and the shop "
        f"keeper handed over {step.phrase}. {step.help_text}"
    )
    demon.meters["quest_progress"] += 1
    demon.memes["relief"] += 1


def return_home(world: World, child: Entity, demon: Entity, form: DemonForm, spell: Spell) -> None:
    demon.meters["transformed"] = 0.0
    demon.meters["magic"] = 0.0
    child.memes["joy"] += 1
    demon.memes["calm"] += 1
    world.say(
        f"Back home, {child.id} and {demon.id} mixed everything together in a bowl "
        f"and whispered the last line of the spell. {spell.qa_text}."
    )
    world.say(
        f"The magic faded in a soft blink. {demon.id} was a little {form.label} again, "
        f"only now {demon.pronoun()} wore a sleepy smile instead of a worried one."
    )


def ending_image(world: World, child: Entity, demon: Entity) -> None:
    world.say(
        f"That evening, {child.id} and {demon.id} sat by the window with warm tea. "
        f"The little demon fit neatly beside the mug, and the whole block looked calm "
        f"through the glass."
    )


def tell(form: DemonForm, quest: list[QuestStep], spell: Spell,
         child_name: str = "Mina", child_type: str = "girl",
         demon_name: str = "Rook", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="hero", traits=["kind", "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    demon = world.add(Entity(id=demon_name, kind="character", type="demon", role="friend", traits=["gentle", "tidy"]))
    world.add(Entity(id="table", type="thing"))
    world.add(Entity(id="bowl", type="thing"))

    make_tap(world, child, demon, form)
    world.para()
    trigger_spell(world, demon, spell)
    for step in quest:
        world.para()
        quest_step(world, child, demon, step)
    world.para()
    return_home(world, child, demon, form, spell)
    world.para()
    ending_image(world, child, demon)

    world.facts.update(
        child=child, parent=parent, demon=demon, form=form, spell=spell,
        quest=quest, transformed=True, completed=True, resolved=True,
    )
    return world


def tell_story(form: DemonForm, quest: list[QuestStep], spell: Spell,
               child_name: str = "Mina", child_type: str = "girl",
               demon_name: str = "Rook", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="hero", traits=["kind", "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    demon = world.add(Entity(id=demon_name, kind="character", type="demon", role="friend", traits=["gentle", "tidy"]))
    world.add(Entity(id="table", type="thing"))
    world.add(Entity(id="bowl", type="thing"))

    make_tap(world, child, demon, form)
    world.para()
    trigger_spell(world, demon, spell)
    for step in quest:
        world.para()
        quest_step(world, child, demon, step)
    world.para()
    return_home(world, child, demon, form, spell)
    world.para()
    ending_image(world, child, demon)
    world.facts.update(child=child, parent=parent, demon=demon, form=form, spell=spell, quest=quest)
    return world


FORMS = {
    "tiny_horned": DemonForm("tiny_horned", "tiny demon", "small demon", "one horn kept flickering", "a tiny bell", "a warm blanket"),
    "cat_like": DemonForm("cat_like", "cat-sized demon", "small demon", "their tail kept flicking like a question mark", "a bowl of milk", "a sunny windowsill"),
    "sleepy": DemonForm("sleepy", "sleepy demon", "small demon", "their wings drooped", "a cup of tea", "a quiet pillow"),
}

QUESTS = {
    "market_loop": [
        QuestStep("tea", "the corner shop", "a cup of tea", "The clerk smiled and poured it into a paper cup.", 1),
        QuestStep("blanket", "the laundromat next door", "a soft blanket", "The owner folded it warm and neat.", 1),
        QuestStep("coin", "the little library desk", "a shiny coin", "The librarian said it liked stories and change.", 1),
    ],
    "garden_loop": [
        QuestStep("tea", "the corner shop", "a cup of tea", "The tea steamed kindly in the takeout cup.", 1),
        QuestStep("leaf", "the pocket garden", "a green leaf", "It was fresh and still smelled like rain.", 1),
        QuestStep("coin", "the little library desk", "a shiny coin", "It winked in the light like it knew the way home.", 1),
    ],
    "bakery_loop": [
        QuestStep("tea", "the bakery counter", "a cup of tea", "The baker set it beside a paper napkin.", 1),
        QuestStep("bun", "the bakery shelf", "a sweet bun", "The smell made everyone calmer right away.", 1),
        QuestStep("coin", "the neighborhood library", "a shiny coin", "The librarian stamped the card and smiled.", 1),
    ],
}

SPELLS = {
    "tea_spell": Spell("tea_spell", 3, 3, "A sprinkle of sparkles rose from the cup and settled over the room", "A weak flicker did almost nothing", "the last drops fit the spell and made the glow turn gentle"),
    "window_spell": Spell("window_spell", 3, 4, "Light from the window bent around the bowl like a ribbon", "The light slipped away and came back wrong", "the last quiet word turned the spell soft and small"),
}

CURATED = [
    StoryParams := None
]

@dataclass
class StoryParams:
    form: str
    quest: str
    spell: str
    child_name: str
    child_type: str
    demon_name: str
    parent_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    demon = f["demon"]
    form = f["form"]
    return [
        f'Write a slice-of-life story for a young child about a friendly demon named {demon.id} and a small magic transformation.',
        f"Tell a gentle quest story where {demon.id} changes into a {form.label} and goes around the neighborhood with a child to fix the spell.",
        f'Write a cozy story that includes the word "demon", a transformation, and a tiny quest that ends at home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, demon, form, quest = f["child"], f["demon"], f["form"], f["quest"]
    answers = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.id} and the demon named {demon.id}. They spend the day together in a small ordinary way, even after the magic starts."
        ),
        QAItem(
            question=f"What changed about {demon.id}?",
            answer=f"{demon.id} was transformed into {form.label}. The change made {demon.id} look smaller and a little worried, so the two of them went on a quest to help."
        ),
        QAItem(
            question="How did they fix the magic?",
            answer=f"They gathered the things from their quest and mixed them together at home. That quiet little routine was enough to settle the spell and bring the demon back to a calmer form."
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip where someone goes looking for something needed to solve a problem. It can be small and ordinary, like visiting a few familiar places."
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form. In stories, magic can make a person or creature look or feel very different for a while."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special power that can make surprising things happen. It might glow, change shapes, or help solve a problem in an unusual way."
        ),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for fid, form in FORMS.items():
        lines.append(asp.fact("form", fid))
        lines.append(asp.fact("needs", fid, form.needs))
    for qid, steps in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for step in steps:
            lines.append(asp.fact("quest_item", qid, step.item.replace(" ", "_")))
    for sid, spell in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("sense", sid, spell.sense))
        lines.append(asp.fact("power", sid, spell.power))
    lines.append(asp.fact("sense_min", MAGIC_SAFE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(S) :- spell(S), sense(S, N), sense_min(M), N >= M.
valid(F, Q, S) :- form(F), quest(Q), spell(S), needs(F, N), quest_item(Q, N), sensible(S).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(s for (s,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life demon magic transformation quest storyworld.")
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--demon-name")
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
    form = args.form or rng.choice(list(FORMS))
    quest = args.quest or rng.choice(list(QUESTS))
    spell = args.spell or rng.choice(list(SPELLS))
    if not reasonableness_gate(FORMS[form], QUESTS[quest], SPELLS[spell]):
        raise StoryError("No valid story matches those choices: the spell must be sensible and the quest must use the form's needed item.")
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(["Mina", "Nico", "Lina", "Arlo", "June", "Theo"])
    demon_name = args.demon_name or rng.choice(["Rook", "Ember", "Pip", "Morrow"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(form, quest, spell, child_name, child_type, demon_name, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(FORMS[params.form], QUESTS[params.quest], SPELLS[params.spell],
                       params.child_name, params.child_type, params.demon_name, params.parent)
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


def _choose_curated() -> list[StoryParams]:
    return [
        StoryParams("sleepy", "market_loop", "tea_spell", "Mina", "girl", "Rook", "mother"),
        StoryParams("cat_like", "garden_loop", "window_spell", "Nico", "boy", "Ember", "father"),
    ]


CURATED = _choose_curated()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible spells: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (form, quest, spell) combos:\n")
        for a, b, c in combos:
            print(f"  {a:12} {b:14} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.child_name} and {p.demon_name}: {p.form} / {p.quest} / {p.spell}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
