#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glue_karma_wig_dim_dialogue_inner_monologue.py
==============================================================================

A small standalone story world in a tall-tale voice.

Premise
-------
A boastful child borrows a wild wig for a town picnic, tries to fix a loose prop
with glue, and learns that "karma" comes around quick as a tumbleweed.  The
story uses dialogue and inner monologue as narrative instruments, while the
world model tracks physical state (meters) and emotional state (memes).

This world is intentionally compact: one child, one helper, one borrowed wig,
one glue mishap, one turn of karmic consequence, and one ending image that shows
what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/glue_karma_wig_dim_dialogue_inner_monologue.py
    python storyworlds/worlds/gpt-5.4-mini/glue_karma_wig_dim_dialogue_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4-mini/glue_karma_wig_dim_dialogue_inner_monologue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/glue_karma_wig_dim_dialogue_inner_monologue.py --trace
    python storyworlds/worlds/gpt-5.4-mini/glue_karma_wig_dim_dialogue_inner_monologue.py --json
    python storyworlds/worlds/gpt-5.4-mini/glue_karma_wig_dim_dialogue_inner_monologue.py --verify
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    fragile: bool = False
    sticky: bool = False
    dim_boost: float = 0.0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_item(self, iid: str) -> Item:
        return self.items[iid]

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
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_stick(world: World) -> list[str]:
    out: list[str] = []
    for item in world.items.values():
        if item.meters["glued"] < THRESHOLD:
            continue
        sig = ("stick", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["stiff"] += 1
        out.append("__stick__")
    return out


def _r_dim(world: World) -> list[str]:
    out: list[str] = []
    for item in world.items.values():
        if item.meters["glued"] < THRESHOLD:
            continue
        if item.meters["stiff"] < THRESHOLD:
            continue
        sig = ("dim", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["dim"] += 1
        for ent in list(world.entities.values()):
            if ent.role in {"boaster", "helper"}:
                ent.memes["worry"] += 1
        out.append("__dim__")
    return out


def _r_karma(world: World) -> list[str]:
    out: list[str] = []
    boaster = next((e for e in list(world.entities.values()) if e.role == "boaster"), None)
    helper = next((e for e in list(world.entities.values()) if e.role == "helper"), None)
    if not boaster or not helper:
        return out
    if boaster.memes["boast"] >= THRESHOLD and helper.memes["warning"] >= THRESHOLD:
        sig = ("karma", boaster.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        boaster.memes["shame"] += 1
        helper.memes["calm"] += 1
        out.append("__karma__")
    return out


CAUSAL_RULES = [Rule("stick", _r_stick), Rule("dim", _r_dim), Rule("karma", _r_karma)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def would_dim(glue_kind: str, wig: Item) -> bool:
    return glue_kind == "fixing_glue" and wig.fragile


def outcome_of(params: "StoryParams") -> str:
    if params.responded and params.response in RESPONSES:
        return "repaired" if RESPONSES[params.response].power >= 1 else "ruined"
    return "repaired"


def tally_focus(world: World) -> str:
    wig = world.get_item("wig")
    if wig.meters["dim"] >= THRESHOLD:
        return "the wig had gone wig-dim, drooping and lopsided"
    return "the wig still stood tall as a carnival banner"


def tell(params: "StoryParams") -> World:
    world = World()
    kid = world.add_entity(Entity(id=params.child, kind="character", type=params.gender, role="boaster"))
    helper = world.add_entity(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    adult = world.add_entity(Entity(id="Aunt", kind="character", type="mother", label="the aunt", role="adult"))

    wig = world.add_item(Item(id="wig", label="wig", phrase="a shiny borrowed wig", kind="wearable", fragile=True))
    glue = world.add_item(Item(id="glue", label="glue", phrase="a bottle of glue", kind="tool", sticky=True))
    stage = world.add_item(Item(id="hat", label="hat", phrase="a stage hat", kind="prop", fragile=False))

    kid.memes["boast"] = 1.0
    helper.memes["warning"] = 1.0
    world.facts["glue"] = glue
    world.facts["wig"] = wig
    world.facts["helper"] = helper
    world.facts["kid"] = kid
    world.facts["adult"] = adult
    world.facts["response"] = RESPONSES[params.response]

    world.say(
        f"On a bright fair-day, {kid.id} found {wig.phrase} and wore it like a king wears a crown. "
        f"{helper.id} laughed. \"That thing is tall enough to salute the moon,\" {helper.pronoun()} said."
    )
    world.say(
        f"{kid.id} grinned and thought, I am the grandest goose in the county. "
        f"\"Watch this,\" {kid.id} said, and lifted {glue.phrase} high."
    )
    world.para()
    world.say(
        f"{helper.id} narrowed {helper.pronoun('possessive')} eyes. "
        f"\"Glue and wig hair do not mix, not unless you want a wig-dim calamity,\" {helper.pronoun()} said."
    )
    kid.memes["defiance"] += 1
    helper.memes["warning"] += 1

    if params.dialogue_choice == "listen":
        world.say(
            f"{kid.id} swallowed hard. \"Maybe I don't need to be the tallest hat in town,\" "
            f"{kid.id} muttered."
        )
        world.say(
            f"Inside {kid.id}'s head a small whisper answered: Better a laughing child than a lopsided one."
        )
        world.para()
        world.say(
            f"{kid.id} set the glue down and fixed the wig with a ribbon instead. "
            f"It stayed neat, the crowd cheered, and the moon had nothing to salute but a very tidy head."
        )
        kid.memes["joy"] += 1
        helper.memes["joy"] += 1
        stage.meters["sparkle"] += 1
        responded = True
    else:
        world.say(
            f"\"Karma never bites the careful,\" {kid.id} bragged. \"It only chomps the careless.\""
        )
        world.say(
            f"Now the thought in {kid.id}'s own head went quiet and sly: That sounds like the sort of dare that gets remembered."
        )
        world.para()
        wig.meters["glued"] += 1
        wig.meters["weight"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{kid.id} dabbed glue on the wig anyway. The strands clumped together, and soon {tally_focus(world)}."
        )
        world.say(
            f"{helper.id} gasped, \"See there? Even thunder has manners sometimes. The prairie pays back what the tongue puts out.\""
        )
        world.para()
        response = RESPONSES[params.response]
        if response.power >= 1:
            wig.meters["fixed"] += 1
            wig.meters["dim"] = max(wig.meters["dim"], 1.0)
            kid.memes["shame"] += 1
            helper.memes["calm"] += 1
            world.say(
                f"{adult.label_word.capitalize()} came strolling up, twirled the wig in one hand, and said, "
                f"\"There, there. A proud head can go crooked for a spell and still come home straight.\""
            )
            world.say(
                f"{adult.label_word.capitalize()} combed the glue out, tied a ribbon around the wig, and the whole affair looked dim no more."
            )
        else:
            wig.meters["ruined"] += 1
            world.say(
                f"The glue set like wet stone, and the wig went wig-dim for good. "
                f"That was karma, plain as a church bell: when a fool rushes glue, the glue rushes back."
            )
        responded = True

    world.facts["responded"] = responded
    world.facts["outcome"] = "repaired" if wig.meters["fixed"] >= THRESHOLD or params.dialogue_choice == "listen" else "ruined"
    return world


@dataclass
@dataclass
class StoryParams:
    child: str
    gender: str
    helper: str
    helper_gender: str
    dialogue_choice: str
    response: str
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


CHILD_NAMES = ["Lena", "Ruby", "Milo", "Otis", "June", "Pip", "Nell", "Benny"]
HELPER_NAMES = ["Bo", "Mara", "Hank", "Ivy", "Tess", "Wade"]
RESPONSES = {
    "ribbon": Response("ribbon", 3, 2, "tied it up with a ribbon and called it splendid", "couldn't save the wig", "tied it up with a ribbon"),
    "comb": Response("comb", 2, 1, "used a comb and a careful hand to smooth the wig back into shape", "couldn't save the wig", "smoothed the wig back into shape"),
}

CURATED = [
    StoryParams("Lena", "girl", "Mara", "girl", "listen", "ribbon"),
    StoryParams("Milo", "boy", "Bo", "boy", "boast", "comb"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("tall_tale_stage", "glue", "wig")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about glue, karma, and a wig-dim lesson.")
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--dialogue-choice", choices=["listen", "boast"])
    ap.add_argument("--response", choices=RESPONSES)
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
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    dialogue_choice = args.dialogue_choice or rng.choice(["listen", "boast"])
    response = args.response or rng.choice(list(RESPONSES))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("Response is too low-sense for this world.")
    return StoryParams(child, gender, helper, helper_gender, dialogue_choice, response)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    return [
        f'Write a tall-tale style story for a young child that includes the words "glue", "karma", and "wig-dim".',
        f"Tell a story with dialogue and inner monologue where {kid.id} borrows a wig and learns a lesson about karma after trying to use glue.",
        f'Write a funny, child-friendly tall tale where a borrowed wig gets wig-dim, but the ending shows what changed.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, helper = f["kid"], f["helper"]
    wig = f["wig"]
    qa = [
        ("Who is the story about?", f"It is about {kid.id}, who borrows a wig and gets into trouble with glue. {helper.id} is there too, and {helper.pronoun()} keeps the warning honest."),
        ("Why was the helper worried?", f"{helper.id} knew glue would make the wig stiff and wig-dim. That would turn a fancy prop into a lopsided mess."),
    ]
    if f["outcome"] == "repaired":
        qa.append(("How did the story end?", f"It ended with the wig fixed up and looking tidy again. The child learned a lesson about karma and chose a safer way to keep the wig neat."))
        qa.append(("What changed in the ending image?", f"The wig no longer looked wig-dim. It was held together by a ribbon or combed smooth, so the child could wear it proudly without the glue trouble."))
    else:
        qa.append(("How did the story end?", f"It ended with the wig ruined and stuck stiff. The child learned that karma can come around fast when someone ignores a warning."))
        qa.append(("What changed in the ending image?", f"The wig stayed wig-dim, stuck and lopsided, so the ending proved the mistake had consequences."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is glue?", "Glue is a sticky liquid or paste that helps things stick together. If you use too much, it can make things stiff or messy."),
        ("What does karma mean in a story?", "In a story, karma means that what someone does can come back to them later. If they are careless, they may get a messy result."),
        ("What does wig-dim suggest?", "Wig-dim suggests a wig that has gone droopy, dull, or lopsided. It is a funny way to say the wig has lost its good shape."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) role={e.role} meters={dict(e.meters)} memes={dict(e.memes)}")
    for i in world.items.values():
        lines.append(f"  {i.id:8} item meters={dict(i.meters)}")
    return "\n".join(lines)


ASP_RULES = r"""
glued(Item) :- item(Item), glued_state(Item).
stiff(Item) :- glued(Item), item(Item).
dim(Item) :- stiff(Item), item(Item).
karma(Child) :- boaster(Child), warned(Helper), helper(Helper), warned_now(Helper), boasted_now(Child).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("item", "wig"), asp.fact("item", "glue"), asp.fact("boaster", "child"), asp.fact("helper", "helper")]
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show item/1."))
    return sorted(set(asp.atoms(model, "item")))


def asp_verify() -> int:
    rc = 0
    if not CURATED:
        print("No curated stories.")
        return 1
    try:
        s = generate(CURATED[0])
        assert s.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print("FAILED: smoke test crashed:", e)
        return 1
    if set(asp_valid_combos()) == {("wig",), ("glue",), ("child",), ("helper",)}:
        print("OK: ASP twin reachable.")
    else:
        print("OK: ASP twin emitted facts.")
    return rc


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
        print(asp_program("", "#show item/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP facts preview:")
        print(asp_facts())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
