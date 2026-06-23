#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/ounce_pregnant_humor_kindness_curiosity_mystery.py
====================================================================================================

A standalone story world for a tiny mystery about an ounce-sized clue, a
pregnant animal, and the gentle tools of humor, kindness, and curiosity.

Seed premise:
- include the words "ounce" and "pregnant"
- keep the tone close to mystery
- make the story child-facing, concrete, and state-driven
- let humor, kindness, and curiosity drive the turn and resolution

The world has a small recurring shape:
1) a curious child notices a strange tiny clue;
2) they investigate a quiet place where a pregnant animal is resting;
3) a harmless misunderstanding makes the mystery feel funny;
4) kindness and curiosity reveal the answer;
5) the ending image proves what changed.

The script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results eagerly and storyworlds/asp lazily
- StoryParams, build_parser, resolve_params, generate, emit, main
- --trace, --qa, --json, --asp, --verify, --show-asp, --all, -n, --seed
- inline ASP twin plus Python reasonableness gate
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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    nook: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    clue_weight: str
    hiding_place: str
    odd_sound: str
    joke_twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PregnantFigure:
    id: str
    type: str
    label: str
    rest_spot: str
    need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    method: str
    reveal: str
    kindness_line: str
    humor_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "bakery": Setting("bakery", "the little bakery", "the flour shelf", "warm", {"search", "weigh", "rest"}),
    "garden": Setting("garden", "the back garden", "the berry bush", "green", {"search", "hide", "rest"}),
    "attic": Setting("attic", "the attic", "the old trunk", "dusty", {"search", "hide"}),
    "clinic": Setting("clinic", "the animal clinic", "the waiting bench", "quiet", {"search", "weigh", "rest"}),
}

MYSTERIES = {
    "tiny_bell": Mystery("tiny_bell", "a tiny bell", "one ounce", "under a cushion", "jingle-jingle", "it turned out to be tied to a kitten toy", {"ounce", "bell", "sound"}),
    "jam_jar": Mystery("jam_jar", "a jam jar", "one ounce", "behind a teacup", "plink-plink", "the jam jar was leaking a sticky trail", {"ounce", "jar", "sticky"}),
    "seed_pouch": Mystery("seed_pouch", "a seed pouch", "one ounce", "inside a basket", "rustle-rustle", "the pouch was being used as a nesting pillow", {"ounce", "pouch", "nest"}),
    "blue_button": Mystery("blue_button", "a blue button", "one ounce", "beside a rug", "tap-tap", "the button had rolled under a chair leg", {"ounce", "button", "rolled"}),
}

PREGNANT_FIGURES = {
    "goat": PregnantFigure("goat", "goat", "a pregnant goat", "a soft hay nest", "quiet hay", {"pregnant", "goat", "animal"}),
    "duck": PregnantFigure("duck", "duck", "a pregnant duck", "a shaded basket", "cool water", {"pregnant", "duck", "animal"}),
    "cat": PregnantFigure("cat", "cat", "a pregnant cat", "a folded blanket", "gentle chin scratches", {"pregnant", "cat", "animal"}),
    "rabbit": PregnantFigure("rabbit", "rabbit", "a pregnant rabbit", "a cozy box", "fresh clover", {"pregnant", "rabbit", "animal"}),
}

RESOLUTIONS = {
    "kind_search": Resolution("kind_search", "search together", "the clue was found without anyone being scolded", "They spoke softly so the resting animal stayed calm.", "The child laughed when the clue turned out to be ordinary.", {"search", "kindness"}),
    "careful_weigh": Resolution("careful_weigh", "use a tiny scale", "the clue was weighed and matched the missing item", "They checked the ounce clue carefully and kindly.", "The scale made the mystery feel like a toy-sized science trick.", {"weigh", "ounce"}),
    "gentle_reveal": Resolution("gentle_reveal", "ask the resting animal's helper", "the helper explained the clue and the missing thing came back", "They asked with kindness instead of barging in.", "The answer was simple, which made the whole mystery a little funny.", {"helper", "kindness"}),
    "funny_mixup": Resolution("funny_mixup", "follow the odd sound", "the odd sound came from a harmless toy, not from trouble", "They followed curiosity and kept their voices low.", "The mystery ended with a giggle and a wagging tail.", {"sound", "humor"}),
}


@dataclass
class StoryParams:
    setting: str
    mystery: str
    figure: str
    resolution: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for f in PREGNANT_FIGURES:
                for r in RESOLUTIONS:
                    combos.append((s, m, f, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld about an ounce clue, a pregnant animal, and kind curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--figure", choices=PREGNANT_FIGURES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.figure is None or c[2] == args.figure)
              and (args.resolution is None or c[3] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, figure, resolution = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(["Mina", "Leo", "Nora", "Theo", "Pia", "Owen"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    helper_name = args.helper_name or rng.choice(["Ruby", "Ben", "June", "Sam", "Iris", "Cal"])
    return StoryParams(
        setting=setting, mystery=mystery, figure=figure, resolution=resolution,
        child_name=child_name, child_type=child_type, helper_name=helper_name, helper_type=helper_type
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    figure = PREGNANT_FIGURES[params.figure]
    resolution = RESOLUTIONS[params.resolution]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name,
                             meters={"distance": 0.0}, memes={"curiosity": 1.0, "kindness": 1.0, "humor": 0.0},
                             attrs={"role": "child"}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name,
                              meters={"distance": 0.0}, memes={"kindness": 1.0}, attrs={"role": "helper"}))
    fig = world.add(Entity(id="figure", kind="character", type=figure.type, label=figure.label,
                           meters={"rest": 1.0}, memes={"comfort": 1.0}, attrs={"rest_spot": figure.rest_spot}))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=mystery.clue, phrase=mystery.clue,
                            meters={"weight": 1.0}, attrs={"weight_word": mystery.clue_weight, "hiding_place": mystery.hiding_place}))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label="a squeaky toy", phrase="a squeaky toy",
                           meters={"noise": 1.0}, attrs={"sound": mystery.odd_sound}))
    world.facts.update(setting=setting, mystery=mystery, figure=figure, resolution=resolution,
                       child=child, helper=helper, fig=fig, clue=clue, toy=toy)

    child.memes["curiosity"] += 1
    child.memes["humor"] += 0.5
    world.say(f"{child.label} found {mystery.clue_weight} of a mystery in {setting.place}.")
    world.say(f"It was {mystery.clue}, and it seemed to have come from {mystery.hiding_place}.")
    world.para()
    world.say(f"{child.label} followed the {mystery.odd_sound} into {figure.rest_spot}.")
    world.say(f"There, {figure.label} was resting, and everyone kept their voices soft.")
    if params.resolution == "funny_mixup":
        child.memes["humor"] += 1
        world.say(f"Then the odd sound turned out to be {toy.label}, which made the whole mystery feel a bit silly.")
    elif params.resolution == "careful_weigh":
        world.say(f"{child.label} set the clue on a tiny scale and saw that it weighed about {mystery.clue_weight}.")
        world.say(f"The number matched the missing item, so the mystery became smaller and clearer.")
    elif params.resolution == "gentle_reveal":
        world.say(f"{helper.label} listened carefully and explained where the missing thing belonged.")
        world.say(f"With one kind question, the clue led back to the right spot.")
    else:
        world.say(f"{child.label} searched slowly until the clue and the sound matched up.")
        world.say(f"It was funny because the mystery had been hiding in plain sight all along.")
    world.para()
    resolution_line = resolution.reveal
    if params.resolution == "kind_search":
        world.say(f"{resolution.kindness_line} {resolution_line.capitalize()}.")
    elif params.resolution == "careful_weigh":
        world.say(f"{resolution.kindness_line} {resolution.humor_line}")
    elif params.resolution == "gentle_reveal":
        world.say(f"{resolution.kindness_line} {resolution_line.capitalize()}.")
    else:
        world.say(f"{resolution.kindness_line} {resolution.humor_line}")
    child.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    fig.meters["rest"] = 1.0
    world.say(f"At the end, {figure.label} stayed cozy in {figure.rest_spot}, and the little clue was no longer lost.")
    return world


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a small child that includes the words "ounce" and "pregnant".',
        f"Tell a gentle mystery where {f['child'].label} notices a one-ounce clue in {f['setting'].place} and helps {f['figure'].label} stay comfortable.",
        f"Write a curious, kind story with a funny clue, a quiet answer, and a pregnant animal resting nearby.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    mystery = f["mystery"]
    figure = f["figure"]
    qa = [
        QAItem(
            question=f"Who was trying to solve the mystery in {setting.place}?",
            answer=f"{child.label} was the one who noticed the clue and followed it. {helper.label} stayed close and helped keep the scene calm."
        ),
        QAItem(
            question=f"What clue did {child.label} find?",
            answer=f"{child.label} found {mystery.clue_weight} of a mystery: {mystery.clue}. It looked small, but it pointed toward {mystery.hiding_place}."
        ),
        QAItem(
            question=f"Why did {child.label} need to be quiet near {figure.label}?",
            answer=f"{figure.label} was pregnant and resting in {figure.attrs['rest_spot']}. {child.label} used kindness so the animal could stay comfortable."
        ),
    ]
    if world.facts["resolution"].id == "careful_weigh":
        qa.append(QAItem(
            question=f"How did the tiny scale help with the clue?",
            answer=f"The scale showed that the clue weighed about one ounce, which matched the missing item. That made the mystery easier to understand without any fuss."
        ))
    elif world.facts["resolution"].id == "gentle_reveal":
        qa.append(QAItem(
            question=f"How did {helper.label} help solve the mystery?",
            answer=f"{helper.label} answered a gentle question and explained where the missing thing belonged. That kind help gave the child the last piece of the puzzle."
        ))
    elif world.facts["resolution"].id == "funny_mixup":
        qa.append(QAItem(
            question="What made the mystery funny?",
            answer=f"The odd sound came from a squeaky toy, not from danger. Once everyone looked closely, the mystery turned into a harmless joke."
        ))
    else:
        qa.append(QAItem(
            question=f"What changed after everyone searched together?",
            answer=f"The clue stopped feeling puzzling because the hidden thing was found. The room stayed quiet, and the pregnant animal kept resting peacefully."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ounce mean?",
            answer="An ounce is a very small unit for weighing things. It helps people notice tiny differences between light objects."
        ),
        QAItem(
            question="What does pregnant mean?",
            answer="Pregnant means an animal or person is expecting a baby to be born later. It is a special time when extra care and kindness matter."
        ),
        QAItem(
            question="Why is curiosity helpful in a mystery?",
            answer="Curiosity makes you look carefully and ask good questions. That helps you find clues and understand what is really happening."
        ),
        QAItem(
            question="Why do kind helpers matter in a story?",
            answer="Kind helpers make a scary or puzzling moment feel safe. They can calm everyone down and help the answer appear more clearly."
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bakery", mystery="tiny_bell", figure="goat", resolution="careful_weigh", child_name="Mina", child_type="girl", helper_name="Ruby", helper_type="mother"),
    StoryParams(setting="garden", mystery="seed_pouch", figure="rabbit", resolution="kind_search", child_name="Leo", child_type="boy", helper_name="Ben", helper_type="father"),
    StoryParams(setting="clinic", mystery="blue_button", figure="cat", resolution="gentle_reveal", child_name="Nora", child_type="girl", helper_name="Iris", helper_type="aunt"),
    StoryParams(setting="attic", mystery="jam_jar", figure="duck", resolution="funny_mixup", child_name="Owen", child_type="boy", helper_name="Cal", helper_type="uncle"),
]


def explain_rejection() -> str:
    return "(No story: this mystery needs a clue, a quiet resting place, and a kind way to solve it.)"


ASP_RULES = r"""
valid(S, M, F, R) :- setting(S), mystery(M), figure(F), resolution(R).
mentions_ounce(M) :- mystery(M), clue_weight(M, ounce).
mentions_pregnant(F) :- figure(F), pregnant(F).
mystery_story(S, M, F, R) :- valid(S, M, F, R), mentions_ounce(M), mentions_pregnant(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_weight", mid, m.clue_weight))
    for fid, f in PREGNANT_FIGURES.items():
        lines.append(asp.fact("figure", fid))
        lines.append(asp.fact("pregnant", fid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP combo gates.")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, figure=None, resolution=None, name=None, child_type=None, helper_name=None, helper_type=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: verify passed with {len(py)} valid combos.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.figure not in PREGNANT_FIGURES or params.resolution not in RESOLUTIONS:
        raise StoryError("(Invalid parameters.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=story_text(world),
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
