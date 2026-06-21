#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gentile_jubilee_dialogue_quest_nursery_rhyme.py
===============================================================================

A standalone storyworld for a tiny nursery-rhyme quest: a gentle child seeks a
missing jubilee token, speaks with a helper and a blocker, and returns in time
for the song-like celebration. The world is built from typed entities with
physical meters and emotional memes, driven by a small causal simulation and a
reasonableness gate.

The seed words are "gentile" and "jubilee"; the style aims for a rhythmic,
child-facing quest with dialogue.
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    detail: str
    echo: str
    quest_need: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    needed_for: str
    sacred: bool = False
    fragile: bool = False
    hidden: bool = False
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
class Action:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    if world.get("seeker").meters["weariness"] < THRESHOLD:
        return out
    sig = ("bump",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("seeker").memes["worry"] += 1
    out.append("__bump__")
    return out


def _r_song(world: World) -> list[str]:
    out: list[str] = []
    if world.get("token").meters["found"] < THRESHOLD:
        return out
    sig = ("song",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hall").meters["jubilee"] += 1
    out.append("__song__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("bump", "social", _r_bump),
    Rule("song", "joy", _r_song),
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


def quest_risk(place: Place, obj: ObjectThing) -> bool:
    return obj.hidden and place.id in {"well", "hill", "lane"}


def sensible_actions() -> list[Action]:
    return [a for a in ACTIONS.values() if a.sense >= 2]


def best_action() -> Action:
    return max(ACTIONS.values(), key=lambda a: a.sense)


def outcome_of(params: "StoryParams") -> str:
    return "done" if ACTIONS[params.action].power >= 1 else "blocked"


def _search(world: World, target: ObjectThing) -> None:
    target.meters["found"] += 1
    target.hidden = False
    propagate(world, narrate=False)


def predict_search(world: World, place: Place, obj: ObjectThing) -> dict:
    sim = world.copy()
    _search(sim, sim.get("token"))
    return {"found": sim.get("token").meters["found"] >= THRESHOLD, "joy": sim.get("hall").meters["jubilee"]}


def tell(place: Place, obj: ObjectThing, action: Action, seeker: str = "Mabel",
         seeker_gender: str = "girl", helper: str = "Ned", helper_gender: str = "boy",
         elder: str = "Mother", elder_gender: str = "mother") -> World:
    world = World()
    hall = world.add(Entity("hall", kind="room", type="room", label="the hall"))
    child = world.add(Entity(seeker, kind="character", type=seeker_gender, role="seeker",
                             traits=["gentle", "curious"]))
    friend = world.add(Entity(helper, kind="character", type=helper_gender, role="helper",
                              traits=["kind", "quick"]))
    parent = world.add(Entity(elder, kind="character", type=elder_gender, role="elder",
                              label="the elder"))
    token = world.add(Entity("token", type="thing", label=obj.label))
    world.facts["place"] = place
    world.facts["obj"] = obj
    world.facts["action"] = action
    world.facts["seeker"] = child
    world.facts["helper"] = friend
    world.facts["parent"] = parent
    world.facts["hall"] = hall
    world.facts["token"] = token

    child.memes["gentleness"] = 5.0
    child.memes["hope"] = 3.0
    friend.memes["helpfulness"] = 4.0

    world.say(
        f"On a bright little morning, {child.id} went along the {place.label}, "
        f"as gentle as a lamb in spring. {place.detail}"
    )
    world.say(
        f'{child.id} said, "{place.quest_need}?" and {friend.id} answered, '
        f'"Let us seek it, quick as a wink."'
    )
    world.para()
    world.say(
        f"{place.echo} \n"
        f'{child.id} looked and looked, then whispered, "{obj.phrase} is nowhere in sight."'
    )
    pred = predict_search(world, place, obj)
    child.memes["worry"] += 1 if pred["found"] else 0
    world.say(
        f'{friend.id} said, "{action.text}"'
    )
    if quest_risk(place, obj):
        child.meters["weariness"] += 1
    _search(world, token)
    world.para()
    if pred["found"]:
        world.say(
            f"{parent.label_word.capitalize()} came with a smile, and the missing {obj.label} was found."
        )
        world.say(
            f"{child.id} lifted it high. The hall filled with jubilee, and the bells seemed to sing."
        )
        world.say(
            f'Then {child.id} said, "{obj.needed_for}," and {friend.id} laughed, '
            f'"A gentile quest indeed."'
        )
    return world


THEMES = {
    "lane": Place(
        "lane", "garden lane",
        "The stones were white, the hedges were neat, and the wind made the leaves nod.",
        "Soft as a whisper, the lane gave back each footstep.",
        "the jubilee ribbon",
        tags={"lane", "quest"},
    ),
    "hill": Place(
        "hill", "green hill",
        "The grass was like a bright quilt, and the sky wore a blue bonnet.",
        "High as a song, the hill sent the breeze around and around.",
        "the jubilee ribbon",
        tags={"hill", "quest"},
    ),
    "well": Place(
        "well", "old well path",
        "The path twinkled with pebbles, and a little gate creaked kindly.",
        "Down below, the well kept a cool hush.",
        "the jubilee key",
        tags={"well", "quest"},
    ),
}

OBJECTS = {
    "ribbon": ObjectThing("ribbon", "ribbon", "a bright jubilee ribbon", "for the song-circle", hidden=True, tags={"ribbon", "jubilee"}),
    "key": ObjectThing("key", "key", "a tiny brass key", "for the music box", hidden=True, tags={"key", "quest"}),
    "star": ObjectThing("star", "star", "a little tin star", "for the cake-top", hidden=True, tags={"star", "jubilee"}),
}

ACTIONS = {
    "ask": Action("ask", 3, 1, "Let us ask the daisies and the ditch for clues.", "could only hush and wait", "asked the flowers for clues", tags={"dialogue"}),
    "sing": Action("sing", 3, 1, "Let us sing a soft rhyme and listen for a ring.", "sang too low to help", "sang a soft rhyme and listened for a ring", tags={"dialogue"}),
    "search": Action("search", 3, 2, "Let us search the path from gate to gate.", "searched too long and came up empty", "searched the path from gate to gate", tags={"quest"}),
}

NAMES = ["Mabel", "Lina", "Pip", "Tessa", "Robin", "Hugo", "Nell", "Bram"]
BOY_NAMES = ["Ned", "Otto", "Theo", "Finn", "Sam", "Jude", "Wren", "Ben"]
TRAITS = ["gentle", "kind", "bright", "cheerful", "patient"]


@dataclass
@dataclass
class StoryParams:
    place: str
    object: str
    action: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in THEMES.items():
        for oid, obj in OBJECTS.items():
            if not quest_risk(place, obj):
                continue
            for aid in ACTIONS:
                combos.append((pid, oid, aid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme quest world.")
    ap.add_argument("--place", choices=THEMES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, action = rng.choice(sorted(combos))
    seeker_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if seeker_gender == "girl" else "girl"
    seeker = args.name or rng.choice(NAMES if seeker_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(BOY_NAMES if helper_gender == "boy" else NAMES)
    elder = args.elder or rng.choice(["Mother", "Father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, obj, action, seeker, seeker_gender, helper, helper_gender, elder, "mother" if elder == "Mother" else "father", trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style quest story that includes the words "gentile" and "jubilee".',
        f"Tell a gentle dialogue quest where {f['seeker'].id} asks for {f['obj'].label} and friends answer in a sing-song way.",
        f"Write a small story for young children where a missing thing is found in time for the jubilee and the ending feels like a rhyme.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["seeker"]
    friend = f["helper"]
    parent = f["parent"]
    obj = f["obj"]
    place = f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {friend.id}, and {parent.label_word}, who all took part in the quest."),
        ("What were they looking for?",
         f"They were looking for {obj.phrase}. It was needed so the jubilee could begin in a happy way."),
        ("What did the children say to one another?",
         f'{child.id} asked, "{place.quest_need}?" and {friend.id} answered with a gentle idea for finding it. Their talk kept the quest moving forward.'),
    ]
    if world.get("token").meters["found"] >= THRESHOLD:
        qa.append((
            "How did the quest end?",
            f"They found the missing {obj.label} and brought it back. After that, the hall filled with jubilee and the children felt bright and proud."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["obj"].tags) | set(world.facts["action"].tags)
    out: list[tuple[str, str]] = []
    if "quest" in tags:
        out.append(("What is a quest?",
                    "A quest is a search for something important. The seeker goes looking, asks questions, and hopes to bring the thing back."))
    if "dialogue" in tags:
        out.append(("What is dialogue?",
                    "Dialogue is when characters speak to one another. Their words help the story move and show how they feel."))
    if "jubilee" in tags:
        out.append(("What is a jubilee?",
                    "A jubilee is a joyful celebration. People may sing, clap, and feel glad together."))
    if "ribbon" in tags:
        out.append(("What is a ribbon?",
                    "A ribbon is a long strip of cloth, often bright and pretty. It can be tied on a present or worn for a celebration."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions -- answerable from the story text =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lane", "ribbon", "ask", "Mabel", "girl", "Ned", "boy", "Mother", "mother", "gentle"),
    StoryParams("hill", "star", "sing", "Lina", "girl", "Finn", "boy", "Father", "father", "kind"),
    StoryParams("well", "key", "search", "Theo", "boy", "Nell", "girl", "Mother", "mother", "bright"),
]


def explain_rejection(place: Place, obj: ObjectThing) -> str:
    return f"(No story: {obj.label} does not fit this quest here.)"


ASP_RULES = r"""
quest_risk(P, O) :- place(P), object(O), hidden(O), risky_place(P).
done :- found(token).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in THEMES.items():
        lines.append(asp.fact("place", pid))
        if pid in {"lane", "hill", "well"}:
            lines.append(asp.fact("risky_place", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.hidden:
            lines.append(asp.fact("hidden", oid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.place], OBJECTS[params.object], ACTIONS[params.action],
                 params.seeker, params.seeker_gender, params.helper, params.helper_gender,
                 params.elder, params.elder_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
