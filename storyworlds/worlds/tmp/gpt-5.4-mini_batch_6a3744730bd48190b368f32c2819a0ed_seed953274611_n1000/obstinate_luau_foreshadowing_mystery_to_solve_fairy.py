#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/obstinate_luau_foreshadowing_mystery_to_solve_fairy.py
======================================================================================

A tiny fairy-tale storyworld about a child who wants to stage a luau, stays
obstinate about the plan, notices foreshadowing clues, and solves a mystery
with the help of a fairy-tale guide. The domain is intentionally small and
classical: one child, one helper, one hidden problem, one reveal, and one safe
ending image that proves what changed.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"risk": 0.0, "reveal": 0.0, "helped": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "worry": 0.0, "stubborn": 0.0, "curiosity": 0.0, "joy": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    setting_line: str
    ending_image: str
    title: str


@dataclass
class Clue:
    id: str
    line: str
    reveals: str


@dataclass
class Mystery:
    id: str
    hidden: str
    cause: str
    reveal_tool: str
    solution_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    line: str
    help_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    theme: Theme
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.theme)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THEMES = {
    "fairy": Theme(
        id="fairy",
        scene="a moonlit glade",
        setting_line="The glade was soft with moss, and a little stream sang near the willow roots.",
        ending_image="By the end, the glade shone with lantern-light, and the child smiled at a solved mystery.",
        title="a fairy tale glade",
    )
}

MYSTERIES = {
    "missing_song": Mystery(
        id="missing_song",
        hidden="the little harp song had gone missing",
        cause="a snail was sleeping on the harp strings",
        reveal_tool="a silver lantern",
        solution_line="The silver lantern showed the snail curled up on the harp, and the mystery was solved at once.",
        tags={"music", "night", "lantern"},
    )
}

CLUES = {
    "wind_chime": Clue(
        id="wind_chime",
        line="A wind chime kept whispering when no one was near, as if it wanted to warn them.",
        reveals="something small was moving in the dark",
    ),
    "petal_trail": Clue(
        id="petal_trail",
        line="A trail of damp petals pointed toward the hollow stump.",
        reveals="someone had passed by the stump",
    ),
}

GUIDES = {
    "fairy": Guide(
        id="fairy",
        label="a tiny fairy",
        line="A tiny fairy with a golden shawl hovered above the clover, bright as a firefly.",
        help_line="The fairy said that clues were little lanterns for patient minds.",
        tags={"fairy", "help"},
    )
}

LUAU_ITEMS = {
    "pineapple": "a bowl of pineapple slices",
    "shells": "a necklace of shells",
    "lantern": "a paper lantern",
}

ENTITY_NAMES = ["Mina", "Lena", "Talia", "Nia", "Iris", "Bram", "Otto", "Pia"]
TRAITS = ["gentle", "curious", "stubborn", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("fairy", "missing_song", clue_id) for clue_id in CLUES]


@dataclass
class StoryParams:
    theme: str
    mystery: str
    clue: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale mystery storyworld with a luau and foreshadowing.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        pool = ["Mina", "Lena", "Talia", "Nia", "Iris", "Pia"]
    else:
        pool = ["Bram", "Otto", "Kai", "Elian", "Noel", "Theo"]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.theme and args.theme not in THEMES:
        raise StoryError("Unknown theme.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, mystery, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, gender)
    helper_gender = args.helper_gender or ("girl" if gender == "boy" else "boy")
    helper = args.helper or _pick_name(rng, helper_gender)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(theme=theme, mystery=mystery, clue=clue, child=child, child_gender=gender, helper=helper, helper_gender=helper_gender, trait=trait)


def _build_world(params: StoryParams) -> World:
    theme = THEMES[params.theme]
    mystery = MYSTERIES[params.mystery]
    clue = CLUES[params.clue]
    world = World(theme)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=["obstinate", params.trait]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["wise", "kind"]))
    fairy = world.add(Entity(id="fairy", kind="character", type="fairy", role="guide", label="the fairy"))
    luau = world.add(Entity(id="luau", kind="thing", type="celebration", label="the luau"))
    song = world.add(Entity(id="song", kind="thing", type="mystery", label="the missing song"))
    child.memes["stubborn"] += 1
    child.memes["hope"] += 1
    world.say(f"{child.id} wanted to host a luau in {theme.scene}, because {child.pronoun()} loved bright things and sweet songs.")
    world.say(theme.setting_line)
    world.say(f"{child.id} lined up {LUAU_ITEMS['pineapple']}, {LUAU_ITEMS['shells']}, and {LUAU_ITEMS['lantern']} for the feast.")
    world.say(f"But a mystery hung over the glade: {mystery.hidden}.")
    world.para()
    world.say(f"{child.id} was obstinate and would not leave the glade until the luau could begin.")
    world.say(f"Then the foreshadowing started to glow. {clue.line}")
    world.say(f"{helper.id} looked at the clue and frowned. {helper.label_word.capitalize()} thought something small and secret was hiding nearby.")
    world.say(f"{fairy.id} appeared. {fairy.line} {fairy.help_line}")
    world.para()
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    world.say(f"{child.id} followed the clue to the hollow stump, carrying {mystery.reveal_tool} like a lantern star.")
    song.meters["reveal"] += 1
    child.meters["helped"] += 1
    world.say(mystery.solution_line)
    world.say(f"At last, everyone found out that {mystery.cause}.")
    world.para()
    child.memes["joy"] += 2
    helper.memes["joy"] += 1
    world.say(f"{child.id} set the luau table under the leaves, and the fruit, shells, and lantern made the glade feel warm and safe.")
    world.say(f"{theme.ending_image}")
    world.facts.update(
        child=child, helper=helper, fairy=fairy, theme=theme, mystery=mystery, clue=clue,
        luau=luau, song=song, outcome="solved", obstinate=True
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a fairy-tale story that includes the words "obstinate" and "luau" and uses a foreshadowing clue to solve a mystery.',
            f"Tell a child-friendly tale where {params.child} is obstinate about starting a luau, notices a clue, and solves the mystery with help from a fairy.",
            f"Write a small fairy tale about a luau, a hidden mystery, and a clue that foreshadows the answer.",
        ],
        story_qa=[
            QAItem(
                question="Why did the child keep looking around the glade?",
                answer=f"{params.child} kept looking because the luau could not truly begin until the mystery was solved. The clue hinted that something small was hiding nearby, so patience turned the worry into a clear answer."
            ),
            QAItem(
                question="What solved the mystery?",
                answer=f"A silver lantern and a careful search solved it. The light revealed that a snail was sleeping on the harp strings, so the strange silence finally made sense."
            ),
            QAItem(
                question="How did the story end?",
                answer=f"It ended with the luau set out in the glade and everyone feeling safe and happy. The solved mystery changed the mood from worried to bright."
            ),
        ],
        world_qa=[
            QAItem(question="What is foreshadowing?", answer="Foreshadowing is a clue that hints at what will happen later. It helps the listener wonder and then feel pleased when the answer appears."),
            QAItem(question="What is a luau?", answer="A luau is a happy feast or party with bright decorations and good food. In fairy tales, it can feel like a cheerful celebration under the sky."),
            QAItem(question="Why do fairy tales often use helpers?", answer="Helpers guide the hero when a problem is puzzling or hidden. They make the story feel magical while still helping the hero solve things wisely."),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id}: type={e.type} role={e.role} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(T, M, C) :- theme(T), mystery(M), clue(C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(theme="fairy", mystery="missing_song", clue="wind_chime", child="Mina", child_gender="girl", helper="Bram", helper_gender="boy", trait="stubborn"),
    StoryParams(theme="fairy", mystery="missing_song", clue="petal_trail", child="Theo", child_gender="boy", helper="Lena", helper_gender="girl", trait="curious"),
]


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t, m, c in combos:
            print(f"  {t:8} {m:14} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
