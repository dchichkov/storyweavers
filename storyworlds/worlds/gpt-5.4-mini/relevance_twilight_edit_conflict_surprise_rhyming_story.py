#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/relevance_twilight_edit_conflict_surprise_rhyming_story.py
==========================================================================================

A standalone storyworld about a child making a twilight rhyme-page, wrestling
with a conflict over an edit, and ending with a small surprise that proves the
changed page finally fits the moment.

Seed words: relevance, twilight, edit
Features: Conflict, Surprise
Style: Rhyming Story
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"ink": 0.0, "neat": 0.0, "tear": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "frustration": 0.0, "joy": 0.0, "surprise": 0.0}

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    name: str
    sky: str
    glow: str

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
class StoryObject:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    writable: bool = True
    relevance_need: bool = True
    meters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"ink": 0.0, "neat": 0.0, "torn": 0.0}

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
class Action:
    id: str
    line: str
    edit_line: str
    effect: str
    conflict_level: int
    surprise: str
    resolves: bool

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
        self.objects: dict[str, StoryObject] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: StoryObject) -> StoryObject:
        self.objects[obj.id] = obj
        return obj

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_object(self, oid: str) -> StoryObject:
        return self.objects[oid]

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
        w.objects = copy.deepcopy(self.objects)
        w.fired = set(self.fired)
        return w


SETTING = Setting("twilight_room", "the little room", "twilight", "a soft lamp glow")


@dataclass
@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    object_id: str
    action_id: str
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


OBJECTS = {
    "poster": StoryObject("poster", "poster", "a poster for the wall", relevance_need=True),
    "poem": StoryObject("poem", "poem page", "a poem page for the scrapbook", relevance_need=True),
    "card": StoryObject("card", "card", "a birthday card", relevance_need=True),
}

ACTIONS = {
    "edit": Action(
        "edit",
        "The page had a bright first line, but one word felt wrong.",
        "The child crossed out the old word and wrote a better one.",
        "The new line matched the twilight feeling much more neatly.",
        conflict_level=1,
        surprise="There, under the lamp, the words finally rhymed.",
        resolves=True,
    ),
    "trim": Action(
        "trim",
        "The lines were long and curly, like a vine.",
        "The child cut one extra line and made the page neat.",
        "The shorter verse fit the space better.",
        conflict_level=0,
        surprise="The page looked tiny and tidy in the end.",
        resolves=True,
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Finn", "Ava", "Eli", "Zoe", "Theo"]
HELPER_NAMES = ["Mom", "Dad", "Rae", "Jules"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for oid, obj in OBJECTS.items():
        if obj.relevance_need:
            for aid, action in ACTIONS.items():
                combos.append((oid, aid))
    return combos


def reason_gate(object_id: str, action_id: str) -> None:
    if object_id not in OBJECTS:
        raise StoryError("Unknown story object.")
    if action_id not in ACTIONS:
        raise StoryError("Unknown action.")
    if not OBJECTS[object_id].relevance_need:
        raise StoryError("This object does not support a relevance-based story.")
    if action_id == "trim" and object_id == "poster":
        return


def _relevance_check(world: World, obj: StoryObject, action: Action) -> bool:
    return obj.relevance_need and action.id == "edit"


def _apply_edit(world: World, child: Entity, obj: StoryObject, action: Action) -> None:
    obj.meters["ink"] += 1
    obj.meters["neat"] += 1
    child.memes["pride"] += 1
    world.say(action.edit_line)
    world.say(action.effect)


def tell(setting: Setting, child: Entity, helper: Entity, obj: StoryObject, action: Action) -> World:
    world = World()
    world.add_entity(child)
    world.add_entity(helper)
    world.add_object(obj)
    child.memes["pride"] = 1.0
    helper.memes["joy"] = 1.0

    world.say(
        f"At {setting.name}, where {setting.sky} came with a silver seam, "
        f"{child.id} sat with {obj.phrase} and a little rhyme to deem."
    )
    world.say(
        f"{child.id} loved the page and loved the page's tune, "
        f"for every soft word twinkled like a star at twilight moon."
    )

    world.para()
    if action.id == "edit":
        world.say(
            f"But one line lost its sparkle, and that made {child.id} frown; "
            f"the rhyme did not feel right for the hush that drifted down."
        )
        child.memes["frustration"] += 1
        helper.memes["surprise"] += 1
        world.say(
            f'{helper.id} said, "An edit can help a poem shine. '
            f"Let's keep the heart, but tune the final line."
        )
        _apply_edit(world, child, obj, action)
        world.para()
        world.say(
            f"Then came the surprise by the lamp's warm, sleepy light: "
            f"a tiny moth landed on the page, and the child laughed, bright."
        )
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
    else:
        world.say(
            f"But the page was crowded, and that made {helper.id} sigh; "
            f"the lines were much too wiggly for the little frame nearby."
        )
        helper.memes["frustration"] += 1
        world.say(
            f'{child.id} trimmed one line with care, and then, oh what a sight: '
            f"the page fit the frame just right, and looked so neat and light."
        )
        obj.meters["neat"] += 1
        world.para()
        world.say(
            f"Then a surprise arrived: the lamp revealed a hidden gold sticker "
            f"at the page's edge, making everyone grin a little bigger."
        )
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        helper.memes["surprise"] += 1

    world.say(
        f"By twilight's end the page was done, and what a change to see: "
        f"{obj.label_word if hasattr(obj, 'label_word') else obj.label} now "
        f"felt just right for the family tree."
    )
    world.facts.update(
        child=child, helper=helper, obj=obj, action=action, setting=setting,
        resolved=True, surprise=True, conflict=(action.id == "edit"),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["obj"]
    action = f["action"]
    return [
        f'Write a rhyming story for a small child that includes the words "relevance", "twilight", and "edit".',
        f"Tell a twilight rhyming story where {child.id} must decide whether to {action.id} a {obj.label} so it feels relevant.",
        f"Write a child-friendly rhyme with a little conflict and a surprise ending about a page that changes at twilight.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    obj = f["obj"]
    action = f["action"]
    qa = [
        QAItem(
            question="What was the child working on?",
            answer=f"{child.id} was working on {obj.phrase}. The page mattered because it was meant to fit the twilight moment and feel relevant.",
        ),
        QAItem(
            question="Why was there conflict in the story?",
            answer=f"There was conflict because the first line did not feel right, and {child.id} wanted to make an edit. That small problem made everyone pause and think before the page could be finished.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The page was edited so it fit the twilight feeling much better, and then the surprise made everyone smile. The ending shows that the right change can make the whole page feel relevant.",
        ),
    ]
    if action.id == "trim":
        qa[1] = QAItem(
            question="Why was there conflict in the story?",
            answer=f"There was conflict because the page looked crowded and needed trimming, even though {child.id} wanted it to stay the same. The edit helped the page fit better, which solved the problem.",
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does twilight mean?",
            answer="Twilight is the soft time between day and night, when the sky grows dim but is not fully dark yet. It often feels calm and a little dreamy.",
        ),
        QAItem(
            question="What is an edit?",
            answer="An edit is a change made to words, pictures, or a page to make it better. People edit when they want something to fit more neatly or clearly.",
        ),
        QAItem(
            question="What is relevance?",
            answer="Relevance means something fits what is needed or what is being talked about. A relevant detail belongs in the story or page because it helps make sense of it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type}) memes={dict(e.memes)} meters={dict(e.meters)}")
    for o in world.objects.values():
        lines.append(f"  {o.id:8} object meters={dict(o.meters)} phrase={o.phrase}")
    return "\n".join(lines)


CURATED = [
    StoryParams("twilight_room", "Mia", "girl", "Mom", "mother", "poem", "edit"),
    StoryParams("twilight_room", "Noah", "boy", "Dad", "father", "poster", "trim"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming twilight story world about relevance, edit, conflict, and surprise.")
    ap.add_argument("--setting", choices=["twilight_room"], default=None)
    ap.add_argument("--child-name", choices=CHILD_NAMES, default=None)
    ap.add_argument("--child-gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper-name", choices=HELPER_NAMES, default=None)
    ap.add_argument("--helper-gender", choices=["girl", "boy", "mother", "father"], default=None)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS, default=None)
    ap.add_argument("--action", dest="action_id", choices=ACTIONS, default=None)
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
    setting = args.setting or "twilight_room"
    object_id = args.object_id or rng.choice(list(OBJECTS))
    action_id = args.action_id or rng.choice(list(ACTIONS))
    reason_gate(object_id, action_id)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_gender = args.helper_gender or rng.choice(["mother", "father", "girl", "boy"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(setting, child_name, child_gender, helper_name, helper_gender, object_id, action_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTING,
        Entity(params.child_name, kind="character", type=params.child_gender, role="child"),
        Entity(params.helper_name, kind="character", type=params.helper_gender, role="helper"),
        copy.deepcopy(OBJECTS[params.object_id]),
        ACTIONS[params.action_id],
    )
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


def valid_combos_asp() -> list[tuple[str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(O, A) :- object(O), action(A), relevance_need(O), supported(O, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", SETTING.id))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.relevance_need:
            lines.append(asp.fact("relevance_need", oid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if action.resolves:
            lines.append(asp.fact("supported", "poster", aid))
            lines.append(asp.fact("supported", "poem", aid))
            lines.append(asp.fact("supported", "card", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_valid = set(asp.atoms(model, "valid"))
    py_valid = set(valid_combos_asp())
    if asp_valid != py_valid:
        print("MISMATCH in valid combos")
        return 1
    sample = generate(CURATED[0])
    if not sample.story or not sample.prompts:
        print("SMOKE TEST FAILED")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in valid_combos_asp():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
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
