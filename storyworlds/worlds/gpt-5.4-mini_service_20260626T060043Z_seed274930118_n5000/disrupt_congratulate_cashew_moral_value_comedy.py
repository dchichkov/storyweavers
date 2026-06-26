#!/usr/bin/env python3
"""
storyworlds/worlds/disrupt_congratulate_cashew_moral_value_comedy.py
===================================================================

A small comedy storyworld about a little disruption, a surprising cashew,
and a moral-value turn toward apologizing, sharing, and congratulating.

Premise:
- A character is trying to host or finish something cheerful.
- A cashew causes a tiny disruption.

Turn:
- Someone makes the choice worse by hiding, teasing, or acting proud.

Resolution:
- The characters tell the truth, fix the mess, and congratulate the helper.

This world is intentionally narrow so every sample feels like a complete,
state-driven comedy with a clear moral value.
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

MORAL_VALUES = {
    "honesty": "honesty",
    "kindness": "kindness",
    "sharing": "sharing",
    "apology": "apology",
    "patience": "patience",
}

PLACES = {
    "kitchen": "the kitchen",
    "classroom": "the classroom",
    "garden": "the garden",
    "stage": "the stage",
}

ACTIVITIES = {
    "bake": "bake tiny cupcakes",
    "paint": "paint a bright sign",
    "build": "build a wobbly tower",
    "practice": "practice a silly song",
}

PROTAGONISTS = {
    "child": {"names": ["Mia", "Toby", "Nina", "Ben", "Lena"], "type": "child"},
    "squirrel": {"names": ["Sparky", "Pip", "Milo", "Nutsy"], "type": "squirrel"},
    "chef": {"names": ["Chef Ruby", "Chef Otto", "Chef Juno"], "type": "chef"},
}

HELPERS = {
    "friend": {"names": ["Ari", "June", "Sam"], "type": "friend"},
    "teacher": {"names": ["Ms. Bean", "Mr. Fox", "Ms. Reed"], "type": "teacher"},
    "neighbor": {"names": ["Mrs. Vale", "Mr. Puck", "Ms. Dot"], "type": "neighbor"},
}

COMEDIC_REACTIONS = [
    "blinked at the tiny trouble",
    "made a face like a squeezed lemon",
    "laughed so hard a spoon nearly danced away",
    "looked at the mess, then at the cashew, then back again",
]

NARRATION_TONES = [
    "silly",
    "bouncy",
    "bright",
    "gentle",
    "playful",
]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "chef", "teacher", "neighbor", "friend", "child"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    activity: str
    value: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_log: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    activity: str
    protagonist: str
    helper: str
    value: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about disruption, cashew, and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--protagonist", choices=PROTAGONISTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--value", choices=MORAL_VALUES)
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


def _choose(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or _choose(rng, sorted(PLACES))
    activity = args.activity or _choose(rng, sorted(ACTIVITIES))
    protagonist = args.protagonist or _choose(rng, sorted(PROTAGONISTS))
    helper = args.helper or _choose(rng, sorted(HELPERS))
    value = args.value or _choose(rng, sorted(MORAL_VALUES))
    if place == "stage" and activity == "bake":
        raise StoryError("The stage is not a sensible place to bake cupcakes in this world.")
    if protagonist == "squirrel" and activity == "practice" and value == "patience":
        # still valid, but if helper is also squirrel we'd get too many squirrel roles
        pass
    return StoryParams(place=place, activity=activity, protagonist=protagonist, helper=helper, value=value)


def _make_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place], activity=ACTIVITIES[params.activity], value=params.value)
    proto_cfg = PROTAGONISTS[params.protagonist]
    helper_cfg = HELPERS[params.helper]
    proto_name = random.choice(proto_cfg["names"])
    helper_name = random.choice(helper_cfg["names"])

    protagonist = world.add(Entity(
        id="protagonist",
        kind="character",
        type=proto_cfg["type"],
        label=proto_name,
        meters={"disruption": 0.0, "mess": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "joy": 0.0, "shame": 0.0, "gratitude": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg["type"],
        label=helper_name,
        meters={"disruption": 0.0},
        memes={"joy": 0.0, "gratitude": 0.0},
    ))
    cashew = world.add(Entity(
        id="cashew",
        kind="thing",
        type="cashew",
        label="cashew",
        phrase="one shiny cashew",
        owner="protagonist",
        meters={"sticky": 0.0, "lost": 0.0},
    ))
    banner = world.add(Entity(
        id="banner",
        kind="thing",
        type="banner",
        label="banner",
        phrase="a cheerful banner",
        owner="helper",
        meters={"fallen": 0.0, "mess": 0.0},
    ))
    world.facts.update(
        protagonist=protagonist,
        helper=helper,
        cashew=cashew,
        banner=banner,
        place=world.place,
        activity=params.activity,
        value=params.value,
        proto_name=proto_name,
        helper_name=helper_name,
    )
    return world


def _narrate_setup(world: World) -> None:
    p = world.facts["protagonist"]
    h = world.facts["helper"]
    place = world.facts["place"]
    activity = world.facts["activity"]
    value = world.facts["value"]
    world.say(
        f"{p.label} was in {place}, trying to {activity} with a very {random.choice(NARRATION_TONES)} grin."
    )
    world.say(
        f"{p.label} cared about {value}, and {h.label} was there to help keep the day cheerful."
    )
    world.say(
        f"On the table sat one little cashew, looking harmless and somehow extremely important."
    )


def _cause_disruption(world: World) -> None:
    p = world.facts["protagonist"]
    h = world.facts["helper"]
    cashew = world.facts["cashew"]
    banner = world.facts["banner"]
    p.meters["disruption"] += 1
    p.meters["mess"] += 1
    cashew.meters["sticky"] += 1
    banner.meters["fallen"] += 1
    h.meters["disruption"] += 1
    p.memes["worry"] += 1
    world.say(
        f"Then the cashew rolled straight off the edge and caused a tiny disruption."
    )
    world.say(
        f"{p.label} {random.choice(COMEDIC_REACTIONS)}, and the banner toppled over like a sleepy ribbon."
    )


def _turn_bad_then_good(world: World) -> None:
    p = world.facts["protagonist"]
    h = world.facts["helper"]
    value = world.facts["value"]
    activity = world.facts["activity"]

    p.memes["pride"] += 1
    p.memes["worry"] += 1
    world.say(
        f"At first {p.label} tried to pretend the cashew had arranged the whole thing on purpose."
    )
    world.say(
        f"But that only made the room feel wobblier, and the joke stopped being funny."
    )
    p.memes["shame"] += 1
    p.memes["pride"] -= 1
    p.memes["worry"] += 1
    world.say(
        f"Then {p.label} took a breath, admitted the mistake, and said sorry."
    )
    h.memes["gratitude"] += 1
    p.memes["gratitude"] += 1
    world.say(
        f"{h.label} helped pick up the banner, and together they set the cashew in a bowl where it could not escape again."
    )
    world.say(
        f"After that, {p.label} could {activity} properly, this time with a calmer smile."
    )
    world.say(
        f"The little disaster became a funny story, and the best part was that honesty fixed the mood."
    )
    world.say(
        f"So {p.label} and {h.label} congratulated each other for making a kind choice."
    )
    world.facts["resolved"] = True
    world.facts["moral"] = value


def tell_story(params: StoryParams) -> World:
    world = _make_world(params)
    _narrate_setup(world)
    world.para()
    _cause_disruption(world)
    world.para()
    _turn_bad_then_good(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["protagonist"]
    h = world.facts["helper"]
    place = world.facts["place"]
    activity = world.facts["activity"]
    value = world.facts["value"]
    return [
        f"Write a funny short story for a young child about a cashew causing a disruption at {place}.",
        f"Tell a comedy story where {p.label} tries to {activity}, then learns {value} with help from {h.label}.",
        "Write a tiny story with a messy little interruption, a sorry, and a happy congratulations at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["protagonist"]
    h = world.facts["helper"]
    place = world.facts["place"]
    activity = world.facts["activity"]
    value = world.facts["value"]
    return [
        QAItem(
            question=f"Where was {p.label} when the cashew caused trouble?",
            answer=f"{p.label} was in {place}, trying to {activity}.",
        ),
        QAItem(
            question=f"What small thing caused the disruption in the story?",
            answer="One little cashew rolled away and caused a tiny disruption.",
        ),
        QAItem(
            question=f"What did {p.label} do to make the mood better again?",
            answer=f"{p.label} told the truth, said sorry, and kept going with {value}.",
        ),
        QAItem(
            question=f"How did {p.label} and {h.label} finish the story?",
            answer=f"They congratulated each other for fixing the problem and keeping the day cheerful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cashew?",
            answer="A cashew is a curved nut people can eat as a snack.",
        ),
        QAItem(
            question="What does it mean to congratulate someone?",
            answer="To congratulate someone means to tell them well done because they did something good.",
        ),
        QAItem(
            question="Why is honesty a good moral value?",
            answer="Honesty is a good moral value because telling the truth helps people trust one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], ""]
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id}: {ent.label} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="bake", protagonist="child", helper="friend", value="honesty"),
    StoryParams(place="classroom", activity="paint", protagonist="squirrel", helper="teacher", value="kindness"),
    StoryParams(place="garden", activity="build", protagonist="chef", helper="neighbor", value="sharing"),
    StoryParams(place="stage", activity="practice", protagonist="child", helper="teacher", value="patience"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in sorted(PLACES):
        lines.append(asp.fact("place", pid))
    for aid in sorted(ACTIVITIES):
        lines.append(asp.fact("activity", aid))
    for vid in sorted(MORAL_VALUES):
        lines.append(asp.fact("value", vid))
    for pid in sorted(PROTAGONISTS):
        lines.append(asp.fact("protagonist", pid))
    for hid in sorted(HELPERS):
        lines.append(asp.fact("helper_role", hid))
    lines.append(asp.fact("disruptor", "cashew"))
    lines.append(asp.fact("congratulation_available"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,R,V,H) :- place(P), activity(A), protagonist(R), value(V), helper_role(H).
story_ready(P,A,R,V,H) :- valid(P,A,R,V,H), disruptor(cashew), congratulation_available.
#show valid/5.
#show story_ready/5.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ready/5."))
    return sorted(set(asp.atoms(model, "story_ready")))


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for p in PLACES:
        for a in ACTIVITIES:
            for r in PROTAGONISTS:
                for v in MORAL_VALUES:
                    for h in HELPERS:
                        if p == "stage" and a == "bake":
                            continue
                        out.append((p, a, r, v, h))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between ASP and Python gates")
        print("only in python:", sorted(py - cl))
        print("only in clingo:", sorted(cl - py))
        return 1
    samples = [generate(StoryParams(*combo)) for combo in sorted(py)[:5]]
    for s in samples:
        if not s.story.strip():
            print("Generated empty story")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combos) and generated stories are non-empty.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.place == "stage" and params.activity == "bake":
        raise StoryError("The stage is not a sensible place to bake cupcakes in this world.")
    world = tell_story(params)
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
        print(asp_program("#show story_ready/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ready/5."))
        combos = sorted(set(asp.atoms(model, "story_ready")))
        print(f"{len(combos)} compatible story combinations.")
        for c in combos[:20]:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.protagonist} / {p.activity} / {p.place} / {p.value}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
