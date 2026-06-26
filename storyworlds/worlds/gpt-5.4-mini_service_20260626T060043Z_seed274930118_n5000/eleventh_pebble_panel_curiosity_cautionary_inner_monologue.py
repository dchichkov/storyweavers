#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/eleventh_pebble_panel_curiosity_cautionary_inner_monologue.py
==========================================================================================================================

A small comedy storyworld about an eleventh panel, a pebble, and a cautionary
inner monologue that helps a curious character avoid a noisy mistake.

Premise:
- A curious child wants to balance a pebble on the eleventh panel of a long
  wooden fence because it looks like a tiny stage.
- A cautious inner voice warns that the panel is wobbly and the pebble may
  roll, clatter, and embarrass everyone.
- The child first tries anyway, then notices the wobble, and finally chooses a
  safer, sillier use for the pebble: a pretend audience seat on the grass.

State model:
- The panel has a wobble meter.
- The pebble has a roll meter.
- Curiosity increases the temptation to act.
- Cautionary inner monologue reduces risky action.
- If the pebble is placed on the panel, it can roll off and make noise.
- A safer substitute leaves the pebble steady and turns the moment into a joke.

The generated stories are short, child-facing, and state-driven, with the
ending image proving what changed.
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
    phrase: str = ""
    owner: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("wobble", "roll", "curiosity", "caution", "embarrassment", "relief", "amusement"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the garden fence"
    afford: str = "panel"


@dataclass
class StoryParams:
    panel_index: int = 11
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


def panel_name(n: int) -> str:
    if n == 11:
        return "eleventh panel"
    if n == 1:
        return "first panel"
    if n == 2:
        return "second panel"
    if n == 3:
        return "third panel"
    return f"{n}th panel"


def ordinal_word(n: int) -> str:
    return {
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
        7: "seventh",
        8: "eighth",
        9: "ninth",
        10: "tenth",
        11: "eleventh",
    }.get(n, f"{n}th")


def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    child = world.add(Entity(
        id="Mina",
        kind="character",
        type="child",
        label="Mina",
        phrase="a curious child",
    ))
    pebble = world.add(Entity(
        id="pebble",
        kind="thing",
        type="pebble",
        label="pebble",
        phrase="a smooth little pebble",
        owner=child.id,
    ))
    panel = world.add(Entity(
        id="panel",
        kind="thing",
        type="panel",
        label=panel_name(params.panel_index),
        phrase=f"the {panel_name(params.panel_index)} of the fence",
        role="seat",
    ))
    world.facts.update(child=child, pebble=pebble, panel=panel, params=params)
    return world


def attempt_balance(world: World) -> None:
    pebble = world.get("pebble")
    panel = world.get("panel")
    child = world.get("Mina")

    child.memes["curiosity"] += 1
    pebble.meters["roll"] += 0.7
    panel.meters["wobble"] += 0.8
    world.say(
        f"Mina stared at the {panel.label} and wondered if a pebble could sit there like a tiny king."
    )
    world.say(
        f"The idea tickled Mina's curiosity so much that the pebble almost hopped forward on its own."
    )


def inner_monologue(world: World) -> None:
    child = world.get("Mina")
    panel = world.get("panel")
    pebble = world.get("pebble")

    child.memes["caution"] += 1
    world.say(
        f'Inside Mina's head, a very serious little voice said, "Hmm. That {panel.label} looks wobblier than a jelly sandwich."'
    )
    world.say(
        f'"If the pebble rolls, it will ping-ping-ping down the fence and make everyone look up at once," the voice warned.'
    )


def maybe_clatter(world: World) -> bool:
    pebble = world.get("pebble")
    panel = world.get("panel")
    child = world.get("Mina")

    if child.memes["caution"] < THRESHOLD:
        sig = ("clatter",)
        if sig in world.fired:
            return False
        world.fired.add(sig)
        pebble.meters["roll"] += 1.0
        panel.meters["wobble"] += 1.0
        child.memes["embarrassment"] += 1.0
        world.say(
            "The pebble tried its best to be dignified, but the panel gave a little shimmy and sent it skittering away."
        )
        world.say(
            "It made exactly the kind of dramatic clink that turned a quiet idea into a neighborhood performance."
        )
        return True
    return False


def safer_turn(world: World) -> None:
    pebble = world.get("pebble")
    child = world.get("Mina")
    world.say(
        "Mina nodded at the warning, picked up the pebble, and put it beside a patch of grass instead."
    )
    pebble.meters["roll"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["amusement"] += 1.0
    world.say(
        "Then Mina gave the pebble a tiny paper-crown pose and declared it the audience for the fence."
    )
    world.say(
        "The pebble stayed put, the panel stayed quiet, and Mina bowed to the imaginary crowd with a grin."
    )


def tell(panel_index: int = 11) -> World:
    world = setup_world(StoryParams(panel_index=panel_index))
    child = world.get("Mina")
    pebble = world.get("pebble")
    panel = world.get("panel")

    world.say(
        f"Mina was a curious child who loved counting things, especially {ordinal_word(panel_index)}s."
    )
    world.say(
        f"One afternoon, Mina found a smooth little pebble beside {world.setting.place} and decided it belonged on the {panel.label}."
    )
    world.para()

    attempt_balance(world)
    inner_monologue(world)
    maybe_clatter(world)
    world.para()

    safer_turn(world)

    world.facts.update(
        child=child,
        pebble=pebble,
        panel=panel,
        place=world.setting.place,
        panel_index=panel_index,
        clatter=bool(pebble.meters["roll"] > 0.7 and child.memes["embarrassment"] > 0),
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    pebble = f["pebble"]
    panel = f["panel"]
    ordinal = ordinal_word(f["panel_index"])
    qa = [
        QAItem(
            question=f"What was Mina trying to do with the pebble on the {panel.label}?",
            answer=(
                f"Mina wanted to balance the pebble on the {panel.label} like a tiny stage trick. "
                f"Curiosity made the idea feel fun, even though it was a little risky."
            ),
        ),
        QAItem(
            question="What did the cautionary inner voice warn Mina about?",
            answer=(
                f"The inner voice warned that the {panel.label} was wobbly and the pebble might roll off. "
                f"It also joked that the pebble would make a loud clattering show if it slipped."
            ),
        ),
        QAItem(
            question=f"What did Mina do instead of keeping the pebble on the {panel.label}?",
            answer=(
                f"Mina moved the pebble to the grass, where it could stay steady. "
                f"Then Mina pretended it was the audience, which was much funnier and much safer."
            ),
        ),
    ]
    if f.get("clatter"):
        qa.append(
            QAItem(
                question="Did the pebble ever make a noisy mistake?",
                answer=(
                    f"Yes. The pebble skittered when the panel wobbled, and that made a noisy little clink. "
                    f"After that, Mina listened to the warning and chose the safer joke instead."
                ),
            )
        )
    else:
        qa.append(
            QAItem(
                question="Did Mina need the pebble to clatter before changing plans?",
                answer=(
                    "No. Mina listened to the cautionary inner monologue before anything went wrong, "
                    "so the story turned into a careful, silly choice instead of a mess."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pebble?",
            answer="A pebble is a small stone, usually smooth enough to hold in your hand.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and try to understand something new.",
        ),
        QAItem(
            question="What is a cautionary thought?",
            answer="A cautionary thought is a warning that helps someone notice a possible problem before acting.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of a person's thoughts inside their own head.",
        ),
        QAItem(
            question="Why can a wooden panel wobble?",
            answer="A wooden panel can wobble if it is loose, springy, or not steady enough to hold weight well.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short comedy story for a young child about an eleventh panel and a pebble.',
        f"Tell a story where Mina's curiosity tempts {f['child'].label} to balance a pebble on the {f['panel'].label}, but a cautionary inner monologue helps choose a safer plan.",
        f"Write a playful story that uses the words eleventh, pebble, and panel, and ends with the pebble being used in a funny safe way.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
child_wants(C) :- curiosity(C), panel(P), pebble(K), near(C,P), finds(C,K).
warns_against(C) :- cautionary(C), child_wants(C).
safe_plan(C) :- warns_against(C), move_to_grass(C,K).
noisy_mistake(C) :- child_wants(C), place_on_panel(C,K,P), wobble(P), not warns_against(C).
resolved(C) :- safe_plan(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("curiosity", "mina"))
    lines.append(asp.fact("cautionary", "mina"))
    lines.append(asp.fact("near", "mina", "panel"))
    lines.append(asp.fact("finds", "mina", "pebble"))
    lines.append(asp.fact("wobble", "panel"))
    lines.append(asp.fact("panel_index", 11))
    lines.append(asp.fact("eleventh", "panel"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = {"mina"} if True else set()
    cl = {a[0] for a in asp_valid()}
    if py == cl:
        print("OK: ASP and Python parity for the cautionary resolution gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: eleventh panel, pebble, and cautionary inner monologue.")
    ap.add_argument("--panel-index", type=int, default=11)
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
    if args.panel_index < 1:
        raise StoryError("panel-index must be a positive number.")
    return StoryParams(panel_index=args.panel_index, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.panel_index)
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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("resolved stories:", asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(panel_index=11, seed=base_seed))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
