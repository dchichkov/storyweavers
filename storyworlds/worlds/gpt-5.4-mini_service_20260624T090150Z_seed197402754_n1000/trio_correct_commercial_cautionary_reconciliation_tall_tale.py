#!/usr/bin/env python3
"""
A tiny storyworld about a traveling trio, a tempting commercial shortcut,
a cautionary mistake, and a reconciliation after the correct choice is found.

This is a standalone storyworld script for the Storyweavers repo.
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


@dataclass
class Character:
    id: str
    role: str
    type: str = "person"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    feature: str
    commercial: str


@dataclass
class TrioState:
    leader: Character
    maker: Character
    runner: Character
    setting: Setting
    cart_loaded: bool = True
    banner_shouted: bool = False
    shortcut_taken: bool = False
    gear_broken: bool = False
    correct_choice: bool = False
    reconciled: bool = False
    cautionary: bool = True
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    name1: str
    name2: str
    name3: str
    seed: Optional[int] = None


PLACES = {
    "river road": Setting(place="river road", feature="a crooked bridge", commercial="a bright wagon-seller"),
    "sunny market": Setting(place="sunny market", feature="a tall signpost", commercial="a loud penny-show"),
    "hill town": Setting(place="hill town", feature="a steep lane", commercial="a traveling store-cart"),
}

NAMES = [
    "Pip", "Mara", "Toby", "June", "Nell", "Otis", "Wren", "Bram", "Luna", "Ezra"
]

ROLES = ["leader", "maker", "runner"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a trio, a commercial shortcut, and a correct fix.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
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


def _pick_names(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    pool = NAMES[:]
    rng.shuffle(pool)
    n1 = args.name1 or pool.pop()
    n2 = args.name2 or pool.pop()
    n3 = args.name3 or pool.pop()
    if len({n1, n2, n3}) < 3:
        raise StoryError("The trio needs three different names.")
    return n1, n2, n3


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    n1, n2, n3 = _pick_names(args, rng)
    return StoryParams(place=place, name1=n1, name2=n2, name3=n3)


def _tall_tale_intro(state: TrioState) -> None:
    state.leader.memes["pride"] = 1
    state.maker.memes["hope"] = 1
    state.runner.memes["cheer"] = 1


def _commercial_temptation(state: TrioState) -> None:
    state.banner_shouted = True
    state.leader.memes["want"] = state.leader.memes.get("want", 0) + 1
    state.shortcut_taken = True
    state.gear_broken = True
    state.cart_loaded = False


def _cautionary_turn(state: TrioState) -> None:
    state.leader.memes["worry"] = 1
    state.maker.memes["regret"] = 1
    state.runner.memes["shock"] = 1


def _correct_choice(state: TrioState) -> None:
    state.correct_choice = True
    state.shortcut_taken = False
    state.gear_broken = False
    state.cart_loaded = True
    state.reconciled = True
    for person in (state.leader, state.maker, state.runner):
        person.memes["relief"] = 1
        person.memes["joy"] = 1


def tell_story(params: StoryParams) -> TrioState:
    setting = PLACES[params.place]
    leader = Character(id=params.name1, role="leader", label=params.name1)
    maker = Character(id=params.name2, role="maker", label=params.name2)
    runner = Character(id=params.name3, role="runner", label=params.name3)
    state = TrioState(leader=leader, maker=maker, runner=runner, setting=setting)

    _tall_tale_intro(state)
    _commercial_temptation(state)
    _cautionary_turn(state)
    _correct_choice(state)

    state.facts = {
        "place": params.place,
        "leader": leader.id,
        "maker": maker.id,
        "runner": runner.id,
        "commercial": setting.commercial,
        "feature": setting.feature,
        "cautionary": state.cautionary,
        "reconciled": state.reconciled,
        "correct_choice": state.correct_choice,
    }
    return state


def render_story(state: TrioState) -> str:
    l, m, r = state.leader.id, state.maker.id, state.runner.id
    place = state.setting.place
    commercial = state.setting.commercial
    feature = state.setting.feature

    parts = [
        f"Long ago, under a sky wide as a quilt, a trio named {l}, {m}, and {r} rolled into {place}.",
        f"They were as lively as a fiddle at a barn dance, and they had a wagon that could whistle in the wind.",
        f"By the road stood {commercial}, calling out a grand promise that sounded easy and shiny.",
        f"{l} listened first and took the shortcut the commercial promised, though {feature} was right there warning them to go slow.",
        f"The tall tale ended in a cautionary tumble: the wagon slipped, the load jolted loose, and all three friends stared at the dust with round eyes.",
        f"Then {m} said the correct thing to do was not to chase the quick trick, but to fix the wheel, mend the straps, and share the work.",
        f"So the trio made peace with one another, set the wagon straight, and reconciled over the honest road home.",
        f"By sunset, {l}, {m}, and {r} were singing again, and the wagon was steadier than a fence post in a thunderstorm.",
    ]
    return " ".join(parts)


def generation_prompts(state: TrioState) -> list[str]:
    f = state.facts
    return [
        f'Write a tall tale about a trio at {f["place"]} that includes a commercial temptation and a correct choice.',
        f"Tell a cautionary story where {f['leader']} learns that a shiny promise can hide trouble.",
        f"Write a reconciliation story about {f['leader']}, {f['maker']}, and {f['runner']} fixing what went wrong together.",
    ]


def story_qa(state: TrioState) -> list[QAItem]:
    f = state.facts
    return [
        QAItem(
            question=f"Who was in the trio at {f['place']}?",
            answer=f"The trio was made of {f['leader']}, {f['maker']}, and {f['runner']}.",
        ),
        QAItem(
            question=f"What commercial thing tried to tempt them?",
            answer=f"{f['commercial']} tried to tempt them with a quick and easy promise.",
        ),
        QAItem(
            question=f"What made the story cautionary?",
            answer="It was cautionary because the trio took the shortcut, the wagon slipped, and they learned to be careful.",
        ),
        QAItem(
            question=f"How did the trio reconcile?",
            answer="They reconciled by fixing the wagon together and choosing the correct, honest way home.",
        ),
    ]


def world_qa(state: TrioState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trio?",
            answer="A trio is a group of three people or things.",
        ),
        QAItem(
            question="What does commercial mean?",
            answer="Commercial means related to buying, selling, or advertising something.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a warning so someone can avoid a mistake.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation is when people make peace again after a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(state: TrioState) -> str:
    bits = [
        "--- world model state ---",
        f"place={state.setting.place}",
        f"feature={state.setting.feature}",
        f"commercial={state.setting.commercial}",
        f"cart_loaded={state.cart_loaded}",
        f"shortcut_taken={state.shortcut_taken}",
        f"gear_broken={state.gear_broken}",
        f"correct_choice={state.correct_choice}",
        f"reconciled={state.reconciled}",
    ]
    for ch in (state.leader, state.maker, state.runner):
        bits.append(f"{ch.id}: memes={dict(ch.memes)}")
    return "\n".join(bits)


ASP_RULES = r"""
trio(X,Y,Z) :- person(X), person(Y), person(Z), X < Y, Y < Z.
commercial_warning(P) :- commercial(P).
correct_choice(P) :- correct(P).
reconciled_story(P) :- corrected(P), peace(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in sorted(PLACES):
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("commercial", p))
        lines.append(asp.fact("correct", p))
        lines.append(asp.fact("peace", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show commercial_warning/1.\n#show correct_choice/1.\n#show reconciled_story/1."))
    atoms = {f"{sym.name}({','.join(str(a) for a in sym.arguments)})" for sym in model}
    expected = {f"commercial_warning({p})" for p in PLACES} | {f"correct_choice({p})" for p in PLACES} | {f"reconciled_story({p})" for p in PLACES}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("ASP mismatch.")
    print("got:", sorted(atoms))
    print("expected:", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    state = tell_story(params)
    story = render_story(state)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(state),
        story_qa=story_qa(state),
        world_qa=world_qa(state),
        world=state,
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
        print(asp_program("#show commercial_warning/1.\n#show correct_choice/1.\n#show reconciled_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for place in sorted(PLACES):
            params = StoryParams(place=place, name1="Pip", name2="Mara", name3="Toby")
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
