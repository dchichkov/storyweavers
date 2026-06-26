#!/usr/bin/env python3
"""
Standalone storyworld: flit, moral value, tall tale.

A tiny, classical simulation in a tall-tale voice:
- a nimble little flitter named Flit
- a tempting boast or shortcut
- a moral value that changes what kind of ending is honest and fitting
- a big, bright resolution with a moral lesson and an ending image

The world is intentionally small and constraint-checked.
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


# ---------------------------------------------------------------------------
# Small domain registries
# ---------------------------------------------------------------------------

MORAL_VALUES = {
    "honesty": {
        "label": "honesty",
        "lesson": "tell the truth",
        "kind": "truth",
        "prompt": "a tall tale about honesty",
    },
    "kindness": {
        "label": "kindness",
        "lesson": "help somebody in need",
        "kind": "help",
        "prompt": "a tall tale about kindness",
    },
    "courage": {
        "label": "courage",
        "lesson": "do the brave thing",
        "kind": "brave",
        "prompt": "a tall tale about courage",
    },
}

SCENES = {
    "bridge": {
        "place": "the crooked bridge over the creek",
        "wonder": "the planks were so long they could tickle a cloud",
        "risk": "the way across was wobbly and squeaky",
    },
    "market": {
        "place": "the little market square",
        "wonder": "the apples were piled as high as a wagon wheel",
        "risk": "everybody was busy and nobody had an extra pair of hands",
    },
    "hill": {
        "place": "the wind-loud hill",
        "wonder": "the grass waved like a green sea",
        "risk": "the gusts were strong enough to steal a hat from a duck",
    },
}

HELPERS = {
    "lamp": {
        "label": "a lantern",
        "effect": "made the dark path shine like sunrise",
        "carry": "carried the lantern",
    },
    "rope": {
        "label": "a rope",
        "effect": "held fast when the wind began to tug",
        "carry": "tied the rope in a knot",
    },
    "basket": {
        "label": "a basket",
        "effect": "gathered the scattered goods before they rolled away",
        "carry": "held the basket steady",
    },
}

CHALLENGES = {
    "lost_apples": {
        "event": "apples spilled from a cart",
        "need": "help gather the apples",
        "shortcut": "claim Flit found them first and keep the praise",
        "truthful_action": "tell the driver what really happened",
        "helpful_action": "call for help and gather the apples",
    },
    "cross_wind": {
        "event": "a strong wind pinched the path",
        "need": "find a safe way across",
        "shortcut": "boast that Flit could outrun the wind",
        "truthful_action": "admit the danger",
        "helpful_action": "ask for a rope and wait for a steady hand",
    },
    "dark_path": {
        "event": "the path turned dark as a spilled ink bottle",
        "need": "light the way",
        "shortcut": "pretend not to be afraid",
        "truthful_action": "say the dark was hard to see through",
        "helpful_action": "bring a lantern and guide the way",
    },
}


# ---------------------------------------------------------------------------
# Shared containers
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    scene: str
    challenge: str
    moral_value: str
    helper: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "person"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


class World:
    def __init__(self, scene: str, challenge: str, moral_value: str, helper: str):
        self.scene = scene
        self.challenge = challenge
        self.moral_value = moral_value
        self.helper = helper
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the scene and helper fit the challenge, and when the
% chosen moral value has a matching resolution.
valid(Scene, Challenge, Moral, Helper) :-
    scene(Scene), challenge(Challenge), moral(Moral), helper(Helper),
    fits(Scene, Challenge), fits_helper(Challenge, Helper), resolves(Moral, Challenge).

% The "flit" premise: a nimble character can take part in any valid story.
flit_story(Scene, Challenge, Moral, Helper) :- valid(Scene, Challenge, Moral, Helper).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for mid in MORAL_VALUES:
        lines.append(asp.fact("moral", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for sid in SCENES:
        for cid in CHALLENGES:
            if sid in {"bridge", "hill"} and cid in {"dark_path", "cross_wind"}:
                lines.append(asp.fact("fits", sid, cid))
            if sid == "market" and cid == "lost_apples":
                lines.append(asp.fact("fits", sid, cid))
    for cid in CHALLENGES:
        for hid in HELPERS:
            if cid == "dark_path" and hid == "lamp":
                lines.append(asp.fact("fits_helper", cid, hid))
            if cid == "cross_wind" and hid == "rope":
                lines.append(asp.fact("fits_helper", cid, hid))
            if cid == "lost_apples" and hid == "basket":
                lines.append(asp.fact("fits_helper", cid, hid))
    for mid in MORAL_VALUES:
        for cid in CHALLENGES:
            if mid == "honesty" and cid == "lost_apples":
                lines.append(asp.fact("resolves", mid, cid))
            if mid == "courage" and cid == "cross_wind":
                lines.append(asp.fact("resolves", mid, cid))
            if mid == "kindness" and cid == "dark_path":
                lines.append(asp.fact("resolves", mid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for sid in SCENES:
        for cid in CHALLENGES:
            if not (
                (sid == "market" and cid == "lost_apples")
                or (sid == "bridge" and cid in {"dark_path", "cross_wind"})
                or (sid == "hill" and cid in {"dark_path", "cross_wind"})
            ):
                continue
            for mid in MORAL_VALUES:
                if not (
                    (mid == "honesty" and cid == "lost_apples")
                    or (mid == "courage" and cid == "cross_wind")
                    or (mid == "kindness" and cid == "dark_path")
                ):
                    continue
                for hid in HELPERS:
                    if (cid == "lost_apples" and hid == "basket") or (
                        cid == "cross_wind" and hid == "rope"
                    ) or (cid == "dark_path" and hid == "lamp"):
                        out.append((sid, cid, mid, hid))
    return out


def explain_rejection(scene: str, challenge: str, moral_value: str, helper: str) -> str:
    return (
        f"(No story: {scene}, {challenge}, {moral_value}, and {helper} do not make a "
        f"reasonable tall-tale lesson together.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about Flit and moral value.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--moral-value", choices=MORAL_VALUES)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.scene is None or c[0] == args.scene)
        and (args.challenge is None or c[1] == args.challenge)
        and (args.moral_value is None or c[2] == args.moral_value)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not filtered:
        if args.scene and args.challenge and args.moral_value and args.helper:
            raise StoryError(explain_rejection(args.scene, args.challenge, args.moral_value, args.helper))
        raise StoryError("(No valid combination matches the given options.)")
    scene, challenge, moral_value, helper = rng.choice(sorted(filtered))
    return StoryParams(scene=scene, challenge=challenge, moral_value=moral_value, helper=helper)


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    chal = CHALLENGES[params.challenge]
    moral = MORAL_VALUES[params.moral_value]
    helper = HELPERS[params.helper]

    world = World(params.scene, params.challenge, params.moral_value, params.helper)
    flit = world.add(Entity(id="Flit", kind="character", type="child", label="Flit"))
    tool = world.add(Entity(id=params.helper, kind="thing", type="thing", label=helper["label"], owner="Flit"))
    world.facts.update(scene=scene, challenge=chal, moral=moral, helper=helper, flit=flit, tool=tool)

    world.say(f"Flit was a little flitter with fast feet and a bigger heart than a barn door.")
    world.say(f"On {scene['place']}, {scene['wonder']}.")
    world.say(f"That was where {chal['event']}, and Flit saw the trouble from a hop and a half away.")

    world.para()
    if params.moral_value == "honesty":
        world.say(f"Flit wanted to brag, but honesty tugged on the sleeve of the day.")
        world.say(f"Instead of telling a shiny lie, Flit said the truth: {chal['truthful_action']}.")
    elif params.moral_value == "kindness":
        world.say(f"Flit saw somebody in a tight spot and felt kindness bloom like a lantern in a porch window.")
        world.say(f"Flit did not stand around polishing pride; Flit chose to {chal['helpful_action']}.")
    else:
        world.say(f"The wind sounded bigger than a brass band, and courage asked Flit to keep moving.")
        world.say(f"Flit did the brave thing and {chal['truthful_action']}, then reached for help with steady paws.")

    world.say(f"With {helper['label']} in hand, Flit {helper['carry']} and the little plan began to work.")
    world.say(f"{helper['effect'].capitalize()}, and the whole place settled down like a tired quilt.")

    world.para()
    if params.challenge == "lost_apples":
        world.say("The apples rolled back into the cart as neatly as marbles in a child's pocket.")
        world.say("Flit got no crown for a false boast, only the warm grin that comes from a true one.")
    elif params.challenge == "cross_wind":
        world.say("The rope held, the gusts lost their temper, and the path stopped wobbling like jelly.")
        world.say("Flit crossed safely, smaller than a thimble and proud as a rooster on parade.")
    else:
        world.say("The lantern turned the dark path into a golden ribbon, and nobody had to squint anymore.")
        world.say("Flit walked home under that soft bright glow, with a calm heart and a brave little stride.")

    world.facts["ending"] = "Moral Value learned"
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a tall tale about Flit that centers on {MORAL_VALUES[world.facts["moral"]["label"] if False else world.moral_value]["prompt"]}.',
        f"Tell a child-friendly tall tale where Flit faces a big little problem and learns {MORAL_VALUES[world.moral_value]['lesson']}.",
        f"Write a short story with the word \"flit\" and a clear moral value ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    moral = MORAL_VALUES[world.moral_value]
    chal = CHALLENGES[world.challenge]
    scene = SCENES[world.scene]
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about Flit, a little flitter with a big heart and quick feet.",
        ),
        QAItem(
            question=f"What problem happened at {scene['place']}?",
            answer=f"{chal['event'].capitalize()}, so Flit had to choose what kind of thing to do next.",
        ),
        QAItem(
            question=f"What moral value did Flit show?",
            answer=f"Flit showed {moral['label']} by choosing to {moral['lesson']} instead of taking the easy shortcut.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the trouble fixed and Flit feeling proud under a bright, peaceful sky.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    moral = MORAL_VALUES[world.moral_value]
    helper = HELPERS[world.helper]
    return [
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth even when a lie would sound easier or shinier.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping somebody and trying to make their day better.",
        ),
        QAItem(
            question="What does courage mean?",
            answer="Courage means doing the brave thing even when you feel a little scared.",
        ),
        QAItem(
            question=f"What is {helper['label']} for?",
            answer=f"{helper['label'].capitalize()} helped solve the problem in the story by making the job easier and safer.",
        ),
        QAItem(
            question=f"What was the lesson in this story?",
            answer=f"The lesson was to {moral['lesson']}.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind}) label={e.label!r} owner={e.owner!r} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(scene="market", challenge="lost_apples", moral_value="honesty", helper="basket"),
    StoryParams(scene="hill", challenge="cross_wind", moral_value="courage", helper="rope"),
    StoryParams(scene="bridge", challenge="dark_path", moral_value="kindness", helper="lamp"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
