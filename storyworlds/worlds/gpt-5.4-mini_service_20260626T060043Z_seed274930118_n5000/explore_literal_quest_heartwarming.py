#!/usr/bin/env python3
"""
storyworlds/worlds/explore_literal_quest_heartwarming.py
=======================================================

A small heartwarming story world about an explore-literal Quest: a child wants
to search for something very specific, follows clues in a gentle way, and ends
with a warm, changed feeling.

The seed words are treated literally:
- explore: the child sets out to look carefully, ask, and search
- literal: the quest is about exact words and exact objects, not a metaphor

The domain stays small on purpose:
- one explorer
- one helper
- one missing item
- one place to search
- one reason the quest matters
- one kind and satisfying result

The prose is state-driven: the world model tracks the missing thing, the search
progress, the emotional tension around a mistake or misunderstanding, and the
resolution when the item is found and returned.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    nooks: tuple[str, ...] = ("bench", "shelf", "window", "doorway")


@dataclass
class Quest:
    id: str
    object_label: str
    object_phrase: str
    object_type: str
    clue_word: str
    search_word: str
    misread_word: str
    place_hint: str
    tension_reason: str
    ending_image: str


@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def _p(subject: Entity, case: str = "subject") -> str:
    return subject.pronoun(case)


def _name(ent: Entity) -> str:
    return ent.id


def _is_gentle_place(setting: Setting) -> bool:
    return setting.place in {"the garden", "the library corner", "the quiet park", "the backyard shed"}


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, nooks=("rose bush", "bench", "birdbath", "gate")),
    "library": Setting(place="the library corner", indoor=True, nooks=("picture shelf", "reading rug", "lamp", "window seat")),
    "park": Setting(place="the quiet park", indoor=False, nooks=("slide", "bench", "tree", "sand patch")),
    "shed": Setting(place="the backyard shed", indoor=True, nooks=("tool hook", "small stool", "box", "doorway")),
}

QUESTS = {
    "kite": Quest(
        id="kite",
        object_label="kite",
        object_phrase="a bright red kite with a tail of ribbons",
        object_type="kite",
        clue_word="ribbons",
        search_word="kite",
        misread_word="light",
        place_hint="high places",
        tension_reason="the wind had carried it away",
        ending_image="the kite tugging softly in the breeze",
    ),
    "book": Quest(
        id="book",
        object_label="book",
        object_phrase="a little picture book with a blue cover",
        object_type="book",
        clue_word="blue",
        search_word="book",
        misread_word="box",
        place_hint="quiet places",
        tension_reason="it had been left somewhere after story time",
        ending_image="the book resting safe and warm on the shelf",
    ),
    "hat": Quest(
        id="hat",
        object_label="hat",
        object_phrase="a soft yellow hat with a stitched star",
        object_type="hat",
        clue_word="star",
        search_word="hat",
        misread_word="cat",
        place_hint="small hiding places",
        tension_reason="it had slipped off during play",
        ending_image="the hat back on a smiling head",
    ),
}


GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ruby", "Ella", "Sage", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Noah", "Leo", "Ari", "Eli", "Sam"]
TRAITS = ["curious", "gentle", "brave", "patient", "kind", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for qname, quest in QUESTS.items():
            if _is_gentle_place(setting):
                combos.append((sname, qname))
    return combos


def explain_rejection(setting: Setting, quest: Quest) -> str:
    return (
        f"(No story: this quest needs a gentle place that supports careful exploring, "
        f"but {setting.place} does not fit the heartwarming tone for a missing {quest.object_label}.)"
    )


def tell(setting: Setting, quest: Quest, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(setting)
    explorer = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    helper_ent = world.add(Entity(id="Helper", kind="character", type=helper, label=("mom" if helper == "mother" else "dad")))
    item = world.add(Entity(
        id=quest.id,
        kind="thing",
        type=quest.object_type,
        label=quest.object_label,
        phrase=quest.object_phrase,
        owner=explorer.id,
        keeper=helper_ent.id,
        location="missing",
    ))

    # Act 1
    world.say(f"{explorer.id} was a {trait} little {explorer.type} who loved to explore.")
    world.say(f"{explorer.id} was on a very literal Quest for {item.phrase}.")
    world.say(f"{explorer.id} and {helper_ent.label} both remembered that {quest.tension_reason}.")

    # Act 2
    world.para()
    world.say(
        f"At {world.setting.place}, {explorer.id} looked carefully at every {quest.place_hint} "
        f"and said, \"I mean the exact {quest.search_word}, not something that only sounds like it.\""
    )
    world.say(
        f"{helper_ent.label} smiled, because the clue word was easy to mix up with {quest.misread_word}, "
        f"but {explorer.id} kept searching with patient eyes."
    )
    world.say(
        f"After checking a few nooks, {explorer.id} found {item.phrase} tucked away where it could wait safely."
    )
    item.location = "found"
    item.carried_by = explorer.id
    explorer.memes["hope"] = explorer.memes.get("hope", 0.0) + 1
    explorer.meters["search"] = explorer.meters.get("search", 0.0) + 1

    # Act 3
    world.para()
    world.say(
        f"{explorer.id} carried it back to {helper_ent.label}, and {helper_ent.label} gave a warm hug."
    )
    world.say(
        f"Soon the {quest.object_label} was back where it belonged, {quest.ending_image}, "
        f"and the whole day felt softer because the quest had ended well."
    )
    explorer.memes["joy"] = explorer.memes.get("joy", 0.0) + 1
    helper_ent.memes["relief"] = helper_ent.memes.get("relief", 0.0) + 1

    world.facts.update(
        explorer=explorer,
        helper=helper_ent,
        item=item,
        quest=quest,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    explorer = f["explorer"]
    item = f["item"]
    quest = f["quest"]
    return [
        f'Write a heartwarming story about a child who goes on a literal quest to explore for {item.phrase}.',
        f"Tell a gentle story where {explorer.id} carefully searches {world.setting.place} for the exact {quest.object_label}.",
        f'Write a short story that includes the word "{quest.clue_word}" and ends with a warm reunion after the search.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    explorer = f["explorer"]
    helper = f["helper"]
    item = f["item"]
    quest = f["quest"]
    setting = f["setting"]

    return [
        QAItem(
            question=f"What kind of quest was {explorer.id} on?",
            answer=f"{explorer.id} was on a literal quest to explore and find {item.phrase} at {setting.place}.",
        ),
        QAItem(
            question=f"Why did {helper.label} and {explorer.id} look carefully instead of rushing?",
            answer=f"They wanted the exact {quest.object_label}, and rushing might have missed the small clue hiding in the room.",
        ),
        QAItem(
            question=f"What was found at the end of the story?",
            answer=f"{item.phrase} was found and brought back safely, so the quest ended with relief and happiness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    quest = f["quest"]
    return [
        QAItem(
            question="What does it mean to explore?",
            answer="To explore means to go look around carefully and discover things you did not know before.",
        ),
        QAItem(
            question="What does literal mean?",
            answer="Literal means exact and plain, not pretend or symbolic.",
        ),
        QAItem(
            question=f"Why can a {quest.object_label} be easy to miss?",
            answer=f"A {quest.object_label} can be easy to miss because it may be small, tucked away, or hidden among other things.",
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
resolved(S, Q) :- setting(S), quest(Q), gentle_place(S).
valid_story(S, Q) :- resolved(S, Q).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sname in SETTINGS:
        lines.append(asp.fact("setting", sname))
        if _is_gentle_place(SETTINGS[sname]):
            lines.append(asp.fact("gentle_place", sname))
    for qname in QUESTS:
        lines.append(asp.fact("quest", qname))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/2."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((s, q) for s, q in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming literal quest story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.setting and args.quest:
        if (args.setting, args.quest) not in combos:
            raise StoryError(explain_rejection(SETTINGS[args.setting], QUESTS[args.quest]))
    choices = [c for c in combos if (not args.setting or c[0] == args.setting) and (not args.quest or c[1] == args.quest)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/2."))
        combos = sorted(set(asp.atoms(model, "resolved")))
        print(f"{len(combos)} compatible (setting, quest) combos:")
        for s, q in combos:
            print(f"  {s:10} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for s, q in valid_combos():
            p = StoryParams(setting=s, quest=q, name="Mina", gender="girl", helper="mother", trait="gentle")
            samples.append(generate(p))
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
            header = f"### {p.name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
