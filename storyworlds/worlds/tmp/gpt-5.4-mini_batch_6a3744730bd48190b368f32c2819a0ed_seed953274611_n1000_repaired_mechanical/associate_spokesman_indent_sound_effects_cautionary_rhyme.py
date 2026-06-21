#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/associate_spokesman_indent_sound_effects_cautionary_rhyme.py
============================================================================================

A tiny nursery-rhyme storyworld about an associate, a spokesman, and a dented
tin tray. The premise is simple: a small speaker wants to show off a noisy trick,
a careful associate warns that the trick will make a dent, and the pair end up
choosing a gentler rhythm instead.

The world is built to satisfy the Storyweavers contract:
- typed entities with meters and memes
- a state-driven simulation rather than frozen prose
- a Python reasonableness gate plus inline ASP twin
- generation prompts, story-grounded QA, and world-knowledge QA
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp

The style aims at a child-facing nursery rhyme, with short rhymes, sound effects,
and a cautionary turn that resolves into a safer ending image.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "dent": 0.0, "rattle": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "care": 0.0, "worry": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "they", "object": "them", "possessive": "their"}
        return mapping[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    place: str
    object: str
    effect: str
    helper: str
    helper_kind: str = "associate"
    speaker_kind: str = "spokesman"
    caution_kind: str = "cautionary"
    rhyme_kind: str = "rhyme"
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


@dataclass
class ItemDef:
    id: str
    label: str
    material: str
    risk: str
    sound: str
    safe_sound: str
    safe_action: str
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
class ResponseDef:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


ITEMS = {
    "tintray": ItemDef(
        id="tintray",
        label="tin tray",
        material="tin",
        risk="dent",
        sound="CLANG!",
        safe_sound="plink-plink",
        safe_action="tap it like a tiny drum",
        tags={"metal", "noise", "dent"},
    ),
    "bell": ItemDef(
        id="bell",
        label="little bell",
        material="brass",
        risk="dent",
        sound="DING-DANG!",
        safe_sound="ding-ding",
        safe_action="ring it softly",
        tags={"metal", "noise", "dent"},
    ),
    "drum": ItemDef(
        id="drum",
        label="toy drum",
        material="hide",
        risk="tear",
        sound="BOOM-BOOM!",
        safe_sound="thump-thump",
        safe_action="pat it with a feather",
        tags={"noise", "drum"},
    ),
}

RESPONSES = {
    "pillow": ResponseDef(
        id="pillow",
        sense=3,
        power=4,
        text="pressed the noisy thing under a soft pillow and hush-hush, the sound grew small",
        fail="pressed a soft pillow on it, but the clatter still rang too loud",
        qa_text="pressed the noisy thing under a soft pillow and hushed the clatter",
        tags={"soft", "quiet"},
    ),
    "cloth": ResponseDef(
        id="cloth",
        sense=4,
        power=5,
        text="wrapped it in a folded cloth and held it still till the rattle was done",
        fail="wrapped it in a cloth, but the rattle kept skipping out",
        qa_text="wrapped it in a folded cloth and held it still",
        tags={"cloth", "quiet"},
    ),
    "move_away": ResponseDef(
        id="move_away",
        sense=5,
        power=3,
        text="carried it to a quiet rug and let the little echoes fade away",
        fail="carried it to a quiet rug, but the clamor was too lively to stop",
        qa_text="carried it to a quiet rug so the echoes could fade",
        tags={"move", "quiet"},
    ),
    "bang": ResponseDef(
        id="bang",
        sense=1,
        power=1,
        text="banged it harder and louder",
        fail="banged it harder and louder, which only made a bigger dent",
        qa_text="banged it harder and louder",
        tags={"unsafe", "noise"},
    ),
}

CAUTIOUS_TRAITS = {"careful", "gentle", "thoughtful", "cautious"}
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Finn", "Theo", "Max", "Sam", "Leo", "Ben"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for item_id, item in ITEMS.items():
        for resp_id, resp in RESPONSES.items():
            if item.risk == "dent" and resp.sense >= 2:
                combos.append((item_id, resp_id))
    return combos


def reasonableness_ok(item: ItemDef, response: ResponseDef) -> bool:
    return item.risk == "dent" and response.sense >= 2


def choose_name(rng: random.Random, kind: str) -> str:
    if kind == "girl":
        return rng.choice(GIRL_NAMES)
    return rng.choice(BOY_NAMES)


def pronounce_rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def tell(world: World, params: StoryParams, item: ItemDef, response: ResponseDef) -> World:
    speaker = world.add(Entity(id="spokesman", kind="character", type="spokesman", role="speaker"))
    helper = world.add(Entity(id="associate", kind="character", type="associate", role="helper"))
    prize = world.add(Entity(id="object", kind="thing", type=item.id, label=item.label))
    room = world.add(Entity(id="room", kind="thing", type="room", label=params.place))

    speaker.memes["pride"] = 2.0
    helper.memes["care"] = 2.0
    world.facts["item"] = item
    world.facts["response"] = response

    world.say(
        f"In {params.place}, there stood a {item.label}, shiny and bright, "
        f"and the spokesman called, “Oh listen now, listen tonight.”"
    )
    world.say(
        f'“I can make a great grand racket!” sang the spokesman with glee, '
        f'“{item.sound} will dance like rain, just wait and see!”'
    )
    world.para()
    world.say(
        f"The associate stepped close with a cautious little grin. "
        f"“Mind the {item.label}, mind the {item.risk}, or a dent may go in.”"
    )
    world.say(
        f"“A cautionary whisper is kinder than a bang, "
        f"for noisy hard knocking makes trouble clang.”"
    )

    if response.id == "bang":
        speaker.memes["pride"] += 1
        prize.meters["dent"] += 2
        prize.meters["noise"] += 1
        world.para()
        world.say(
            f"But the spokesman chose bang-bang bravado instead, "
            f"and {item.label} went bump with a bump on its head."
        )
        world.say(
            f"CLANG! went the tray, and a dent popped in quick; "
            f"the rhyme turned quite sorry, and the trick was not slick."
        )
        world.say(
            "The associate frowned and shook their head slow. "
            "“That is the wrong road, and now we all know.”"
        )
    else:
        world.facts["used_safe"] = True
        speaker.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.para()
        world.say(
            f"The spokesman listened, then softened his tone. "
            f"Together they chose a small gentler zone."
        )
        world.say(
            f"They {response.text}, and the noisy part passed; "
            f"{item.safe_sound} went the rhythm, soft, small, and fast."
        )
        world.say(
            f"No dent in the {item.label}, no bump and no bruise; "
            f"the pair kept their promise, the safer thing to use."
        )
        world.say(
            f"So the spokesman and associate smiled side by side, "
            f"and nursery-rhyme music went swish through the ride."
        )

    world.facts.update(
        speaker=speaker,
        helper=helper,
        prize=prize,
        room=room,
        outcome="safe" if response.id != "bang" else "dented",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: ItemDef = f["item"]  # type: ignore[assignment]
    return [
        f'Write a nursery-rhyme story that includes the words "associate", '
        f'"spokesman", and "indent" or "dent" in a child-safe way.',
        f"Tell a cautionary rhyme where the spokesman wants to make noise with a "
        f"{item.label}, but the associate warns that a hard hit will make a dent.",
        f"Write a short rhyming story with sound effects like {item.sound} and a "
        f"gentle ending where the children choose a safer sound.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item: ItemDef = f["item"]  # type: ignore[assignment]
    response: ResponseDef = f["response"]  # type: ignore[assignment]
    outcome = f["outcome"]
    qa = [
        (
            "Who are the story characters?",
            "The story is about a spokesman and an associate. "
            "The spokesman wants to make noise, and the associate tries to keep things safe.",
        ),
        (
            "What was the spokesman tempted to do?",
            f"The spokesman wanted to use the {item.label} for a loud performance. "
            f"The sound effect {item.sound} shows how noisy the idea felt.",
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                "How did the associate help?",
                f"The associate warned that a hard hit could make a dent, and the spokesman listened. "
                f"They used a gentler plan by {response.qa_text}.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with no dent in the {item.label}. "
                f"The children kept the rhythm small and kind.",
            )
        )
    else:
        qa.append(
            (
                "What happened when the spokesman ignored the warning?",
                f"The hard bang made a dent in the {item.label}. "
                f"The cautionary part of the rhyme showed why the softer choice was wiser.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a dented {item.label}, and the associate felt upset. "
                f"The rhyme teaches that loud trouble can leave a mark.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item: ItemDef = f["item"]  # type: ignore[assignment]
    response: ResponseDef = f["response"]  # type: ignore[assignment]
    tags = set(item.tags) | set(response.tags)
    out: list[tuple[str, str]] = []
    if "dent" in tags:
        out.append(
            (
                "What is a dent?",
                "A dent is a little pushed-in mark or hollow on a surface. "
                "It can happen when something is hit too hard.",
            )
        )
    if "quiet" in tags:
        out.append(
            (
                "Why do people choose a quieter way sometimes?",
                "A quieter way can keep things safe and calm. "
                "It helps avoid damage and big noisy trouble.",
            )
        )
    if "soft" in tags:
        out.append(
            (
                "What does soft mean?",
                "Soft means gentle and not hard. "
                "Soft things usually make less noise and less trouble.",
            )
        )
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
        lines.append(f"  {e.id:10} ({e.kind:8}) label={e.label!r} role={e.role!r} meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(item: ItemDef, response: ResponseDef) -> str:
    return (
        f"(No story: the chosen response is too weak or the item is not a dent-risk. "
        f"Try a quieter, safer response with a dent-prone object.)"
    )


CURATED = [
    StoryParams(
        place="the toy room",
        object="tintray",
        effect="noise",
        helper="Mia",
        helper_kind="associate",
        speaker_kind="spokesman",
        caution_kind="cautionary",
        rhyme_kind="rhyme",
    ),
    StoryParams(
        place="the sunny hall",
        object="bell",
        effect="sound",
        helper="Leo",
        helper_kind="associate",
        speaker_kind="spokesman",
        caution_kind="cautionary",
        rhyme_kind="rhyme",
    ),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.risk == "dent":
            lines.append(asp.fact("risk_dent", iid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(I, R) :- risk_dent(I), response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(object=None, effect=None, helper=None, place=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception:
        rc = 1
        traceback.print_exc()
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with a cautionary turn.")
    ap.add_argument("--object", choices=ITEMS.keys())
    ap.add_argument("--response", choices=RESPONSES.keys())
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
    item_id = args.object or rng.choice(list(ITEMS.keys()))
    resp_id = args.response or rng.choice([k for k, v in RESPONSES.items() if v.sense >= 2])
    item = ITEMS[item_id]
    resp = RESPONSES[resp_id]
    if not reasonableness_ok(item, resp):
        raise StoryError(explain_rejection(item, resp))
    return StoryParams(
        place="the playroom",
        object=item_id,
        effect="sound",
        helper="Mia",
        helper_kind="associate",
        speaker_kind="spokesman",
        caution_kind="cautionary",
        rhyme_kind="rhyme",
    )


def generate(params: StoryParams) -> StorySample:
    if params.object not in ITEMS:
        raise StoryError("Unknown object.")
    item = ITEMS[params.object]
    response_id = "cloth"
    if params.effect == "sound":
        response_id = "cloth"
    response = RESPONSES[response_id]
    world = tell(World(), params, item, response)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible object/response combos:")
        for item_id, resp_id in combos:
            print(f"  {item_id} {resp_id}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
