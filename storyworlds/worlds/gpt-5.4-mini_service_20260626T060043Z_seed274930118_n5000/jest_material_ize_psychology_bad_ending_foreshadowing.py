#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little comedy club"
    afford: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    mess: str
    foreshadow: str
    warning: str


@dataclass
class StoryParams:
    setting: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "club": Setting(place="the little comedy club", afford={"jest"}),
    "classroom": Setting(place="the classroom", afford={"jest"}),
    "kitchen": Setting(place="the kitchen", afford={"jest"}),
}

TOOLS = {
    "jest_book": Tool(
        id="jest_book",
        label="jest book",
        phrase="a bright jest book with tiny punch lines",
        effect="the jokes started bouncing around the room",
        mess="laughs",
        foreshadow="Its cover kept wiggling as if the jokes inside were trying to escape.",
        warning="If the jokes got loose, they might turn everything silly.",
    ),
    "giggling_bell": Tool(
        id="giggling_bell",
        label="giggling bell",
        phrase="a shiny bell that rang with giggles",
        effect="the bell made the air feel extra tingly",
        mess="giggles",
        foreshadow="Every time it chimed, a few crumbs on the table jumped.",
        warning="A bell that tickles feelings can make a whole room wobble.",
    ),
    "psychology_mirror": Tool(
        id="psychology_mirror",
        label="psychology mirror",
        phrase="a round psychology mirror that showed your thoughts",
        effect="the mirror made thoughts look almost real",
        mess="ideas",
        foreshadow="When nobody looked, the mirror flashed like it was listening.",
        warning="A thoughty mirror can make a joke feel bigger than expected.",
    ),
}

NAMES = ["Milo", "Pia", "Nina", "Toby", "Luna", "Zed"]
TRAITS = ["cheerful", "sly", "silly", "curious", "confident"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedy storyworld about jest, material-ize, and psychology.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TOOLS]


CURATED = [
    StoryParams(setting="club", tool="jest_book", name="Milo", gender="boy", parent="mother", trait="silly"),
    StoryParams(setting="classroom", tool="giggling_bell", name="Pia", gender="girl", parent="father", trait="curious"),
    StoryParams(setting="kitchen", tool="psychology_mirror", name="Nina", gender="girl", parent="mother", trait="cheerful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.tool and (args.setting, args.tool) not in combos:
        raise StoryError("No valid story matches that setting and tool.")
    setting = args.setting or rng.choice(list(SETTINGS))
    tool = args.tool or rng.choice(list(TOOLS))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES[:3] if gender == "boy" else NAMES[3:])
    return StoryParams(setting=setting, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


def _do_jest(world: World, child: Entity, tool: Tool) -> None:
    child.memes["glee"] = child.memes.get("glee", 0) + 1
    child.meters["nonsense"] = child.meters.get("nonsense", 0) + 1


def _materialize(world: World, child: Entity, tool: Tool) -> bool:
    if child.meters.get("nonsense", 0) < 1:
        return False
    child.meters["mess"] = child.meters.get("mess", 0) + 1
    world.facts["materialized"] = True
    return True


def tell(setting: Setting, tool: Tool, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"hope": 1}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prop = world.add(Entity(id="Prop", type=tool.id, label=tool.label, phrase=tool.phrase, owner=child.id, caretaker=parent.id))
    child.meters["nonsense"] = 0
    child.meters["mess"] = 0

    world.say(f"{name} was a {trait} little {gender} who loved a good jest more than a cookie jar on a low shelf.")
    world.say(f"At {setting.place}, {name} found {tool.phrase}. {tool.foreshadow}")
    world.say(f"{name} grinned and whispered, \"If I jest hard enough, maybe the funny part will material-ize.\"")
    world.para()

    world.say(f"That day, {name} and {name}'s {parent_type} went to {setting.place}.")
    world.say(f"{name} wanted to use the {tool.label}, but {name}'s {parent_type} gave a cautionary look. \"Careful,\" they said. \"A joke can be a tiny seed.\"")
    world.say(tool.warning)
    _do_jest(world, child, tool)
    world.say(f"{name} told a bigger and bigger joke, and {tool.effect}.")
    if _materialize(world, child, tool):
        world.say(f"Then the joke really did material-ize: a parade of giggles popped out of nowhere and knocked over the napkins.")
    world.para()

    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(f"{name} tried to laugh it off, but the mirror of psychology had made the silliness feel real.")
    world.say(f"The giggles bounced from chair to chair until even the teacher's hat was trembling.")
    world.say(f"In the end, the room was too slippery with laughter, the snack tray tipped, and nobody could find the punch line anymore.")
    world.say(f"{name}'s {parent_type} sighed, swept up the crumbs, and said, \"Next time, make sure your jest stays a joke.\"")

    world.facts.update(child=child, parent=parent, prop=prop, tool=tool, setting=setting, bad_ending=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedic story for a young child about a {f["child"].type} named {f["child"].id} and a {f["tool"].label}.',
        f'Tell a cautionary story where a jest goes too far and starts to material-ize because of psychology.',
        f'Write a funny story with foreshadowing, a warning, and a bad ending at {f["setting"].place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {child.id} try to do with the {tool.label}?",
            answer=f"{child.id} tried to jest with it so hard that the funny idea would material-ize.",
        ),
        QAItem(
            question=f"Why did {parent.type} {parent.id if hasattr(parent,'id') else 'the parent'} warn {child.id}?",
            answer=f"The warning was cautionary: the jokes could become real, and then the room would turn messy.",
        ),
        QAItem(
            question="Did the story have a happy ending?",
            answer="No. It had a bad ending, because the giggles got loose and made a mess that had to be cleaned up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a jest?",
            answer="A jest is a joke or playful remark meant to make people laugh.",
        ),
        QAItem(
            question="What does material-ize mean?",
            answer="To material-ize means to become real or take shape in the world.",
        ),
        QAItem(
            question="What is psychology?",
            answer="Psychology is the study of how thinking and feelings work.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting(S),tool(T)) :- setting(S), tool(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    got = sorted(set(asp.atoms(model, "valid")))
    exp = sorted((f"setting({s})", f"tool({t})") for s, t in valid_combos())
    # Compare via stringified tuples for a simple parity gate.
    got_s = sorted(str(x) for x in got)
    exp_s = sorted(str(x) for x in exp)
    if got_s == exp_s:
        print(f"OK: ASP parity check passed for {len(exp_s)} combos.")
        return 0
    print("MISMATCH")
    print("got:", got_s)
    print("exp:", exp_s)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TOOLS[params.tool], params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
