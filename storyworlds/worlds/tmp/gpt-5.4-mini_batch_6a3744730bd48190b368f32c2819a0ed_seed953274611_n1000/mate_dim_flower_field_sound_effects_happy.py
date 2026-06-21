#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mate_dim_flower_field_sound_effects_happy.py
============================================================================

A standalone storyworld for a tiny myth-flavored flower-field tale.

Premise:
- A small village tends a flower field that has gone dim.
- A child or helper hears a legend, gathers a companion ("mate"), and uses
  sound effects as a ritual instrument to wake the field.
- The world model tracks light, bloom, music, trust, and joy.
- A happy ending arrives when the field brightens and the flowers open.

This world follows the shared Storyweavers contract:
- stdlib only
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    title: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "daughter"}
        male = {"boy", "father", "dad", "man", "brother", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Rune:
    id: str
    phrase: str
    sound: str
    light_gain: float
    joy_gain: float
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    type: str = "spirit"
    courage: int = 4
    hymn: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class FlowerField:
    id: str
    label: str
    dimness: float
    bloom_need: int
    bloom_image: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_brighten(world: World) -> list[str]:
    out: list[str] = []
    field = world.get("field")
    for ent in world.entities.values():
        if ent.meters["sound"] < THRESHOLD:
            continue
        sig = ("brighten", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        field.meters["light"] += 1
        field.meters["bloom"] += 1
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["hope"] += 1
        out.append("__spark__")
    return out


def _r_joy(world: World) -> list[str]:
    out: list[str] = []
    field = world.get("field")
    if field.meters["light"] < THRESHOLD or field.meters["bloom"] < THRESHOLD:
        return out
    sig = ("joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["joy"] += 1
    out.append("__happy__")
    return out


CAUSAL_RULES = [Rule("brighten", _r_brighten), Rule("joy", _r_joy)]


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


def eligible_runes() -> list[Rune]:
    return [r for r in RUNES.values() if r.light_gain >= 1 and r.joy_gain >= 1]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not eligible_runes():
        return combos
    for field_id in FIELDS:
        for companion_id in COMPANIONS:
            for rune_id in RUNES:
                if field_id == "flower_field" and rune_id in RUNES:
                    combos.append((field_id, companion_id, rune_id))
    return combos


@dataclass
class StoryParams:
    field: str
    companion: str
    rune: str
    child_name: str
    child_gender: str
    child_role: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic flower-field storyworld with sound effects and a happy ending."
    )
    ap.add_argument("--field", choices=FIELDS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--rune", choices=RUNES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["herder", "listener", "gardener", "wanderer"])
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


def explain_rejection(rune: Rune) -> str:
    return f"(No story: the rune {rune.id} does not fit the mythic flower-field blessing.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.rune and args.rune not in RUNES:
        raise StoryError("(Unknown rune.)")
    if args.rune and RUNES[args.rune].light_gain < 1:
        raise StoryError(explain_rejection(RUNES[args.rune]))

    combos = [c for c in valid_combos()
              if (args.field is None or c[0] == args.field)
              and (args.companion is None or c[1] == args.companion)
              and (args.rune is None or c[2] == args.rune)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    field_id, companion_id, rune_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    role = args.role or rng.choice(ROLES)
    return StoryParams(
        field=field_id,
        companion=companion_id,
        rune=rune_id,
        child_name=name,
        child_gender=gender,
        child_role=role,
    )


def tell(field: FlowerField, companion: Companion, rune: Rune, child: Entity) -> World:
    world = World()
    child = world.add(child)
    spirit = world.add(Entity(
        id=companion.id,
        kind="character",
        type=companion.type,
        label=companion.label,
        role="mate",
        title="mate",
        traits=["kind", "steady"],
        tags=set(companion.tags),
    ))
    fld = world.add(Entity(id="field", kind="thing", type="place", label=field.label))
    fld.meters["light"] = field.dimness
    fld.meters["bloom"] = 0.0

    child.memes["wonder"] = 1.0
    child.memes["worry"] = 0.0
    spirit.memes["courage"] = float(companion.courage)

    world.say(
        f"In the old days, when the flower field was dim, {child.id} walked beneath "
        f"the green stems and whispered to the wind. The blossoms bowed as if they were "
        f"waiting for a remembered name."
    )
    world.say(
        f"Then {child.id} met {spirit.label_word}, the {companion.label}, and the two of them "
        f"looked toward the sleeping field."
    )
    world.para()
    world.say(
        f'"{rune.phrase}," said {child.id}, and the little glyph shimmered like a secret in the grass.'
    )
    world.say(
        f'{spirit.id} lifted {spirit.pronoun("possessive")} hands and answered, "{rune.sound}"'
    )
    child.meters["sound"] += 1
    child.memes["hope"] += rune.joy_gain
    spirit.meters["sound"] += 1
    spirit.memes["hope"] += 1
    world.say(f"The sound rolled out over the petals: {rune.sound}!")
    propagate(world, narrate=False)
    world.para()

    if fld.meters["light"] >= THRESHOLD and fld.meters["bloom"] >= THRESHOLD:
        world.say(
            f"The field listened. Little by little, the gray hush lifted, and the flowers opened "
            f"wide as sunrise. Gold pollen twirled in the air like bright dust."
        )
        world.say(
            f"{child.id} laughed, and {spirit.id} laughed with {child.id}, while the meadow "
            f"glowed around them as if the earth itself had remembered how to sing."
        )
    else:
        world.say(
            f"For a moment the field only trembled, and the petals stayed shut. But the sound had "
            f"already begun to wake the roots, and the dawn was on its way."
        )
        world.say(
            f"{child.id} and {spirit.id} waited together, patient as stones, until the blossoms "
            f"began to shine."
        )

    world.facts.update(
        child=child,
        spirit=spirit,
        rune=rune,
        field_cfg=field,
        field_entity=fld,
        outcome="happy",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story in a flower field that includes the word "{f["rune"].id}" and a bright sound effect.',
        f"Tell a happy ending tale where {f['child'].id} and the {f['spirit'].label} wake the flower field with a chant and a sound effect.",
        f'Write a gentle myth for children set in a flower field, with "{f["rune"].sound}" echoing through the blossoms.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, spirit, rune = f["child"], f["spirit"], f["rune"]
    fld = f["field_entity"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {spirit.label_word}, who worked together in the flower field. Their shared effort is what wakes the field."),
        ("What made the flowers wake up?",
         f"Their chant and the sound effect, {rune.sound}, rolled across the field. That sound helped the field gather light and bloom."),
        ("How did the story end?",
         f"It ended happily, with the dim field turning bright and the blossoms opening wide. The last image is of the meadow shining around them."),
        ("What changed in the field?",
         f"The field grew brighter and began to bloom. It went from dim and waiting to full of light and open flowers."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a flower field?",
         "A flower field is a wide place where many flowers grow together. It can look like a bright blanket of color."),
        ("Why do sound effects matter in a mythic story?",
         "Sound effects help the story feel alive and ceremonial. They can make a moment feel powerful, like a little spell or chant."),
        ("What is a happy ending?",
         "A happy ending is when the problem gets solved in a good way. The story finishes with safety, joy, or a new hope."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


FIELDS = {
    "flower_field": FlowerField(
        id="flower_field",
        label="the flower field",
        dimness=0.0,
        bloom_need=1,
        bloom_image="wide blossoms",
        tags={"flower_field", "myth", "happy"},
    )
}

COMPANIONS = {
    "mate": Companion(
        id="mate",
        label="mate",
        type="spirit",
        courage=5,
        hymn="a low humming hymn",
        tags={"mate-dim", "myth", "sound"},
    ),
    "guide": Companion(
        id="guide",
        label="guide",
        type="spirit",
        courage=6,
        hymn="a bright guiding chant",
        tags={"mate-dim", "myth", "sound"},
    ),
}

RUNES = {
    "mate_dim": Rune(
        id="mate-dim",
        phrase="mate-dim",
        sound="dum-dum-dim",
        light_gain=1.0,
        joy_gain=1.0,
        tags={"mate-dim", "sound", "myth"},
    ),
    "hush_bloom": Rune(
        id="hush-bloom",
        phrase="hush-bloom",
        sound="shaa-ring",
        light_gain=1.0,
        joy_gain=1.0,
        tags={"sound", "myth"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Sera", "Iris", "Nina", "Asha"]
BOY_NAMES = ["Orin", "Taro", "Eren", "Kian", "Pavel", "Jorin"]
ROLES = ["herder", "listener", "gardener", "wanderer"]

CURATED = [
    StoryParams(field="flower_field", companion="mate", rune="mate_dim", child_name="Lina", child_gender="girl", child_role="listener"),
    StoryParams(field="flower_field", companion="guide", rune="hush_bloom", child_name="Orin", child_gender="boy", child_role="herder"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid in FIELDS:
        lines.append(asp.fact("field", fid))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    for rid, r in RUNES.items():
        lines.append(asp.fact("rune", rid))
        lines.append(asp.fact("light_gain", rid, int(r.light_gain)))
        lines.append(asp.fact("joy_gain", rid, int(r.joy_gain)))
    return "\n".join(lines)


ASP_RULES = r"""
eligible(R) :- rune(R), light_gain(R, L), joy_gain(R, J), L >= 1, J >= 1.
valid(F, C, R) :- field(F), companion(C), eligible(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos disagree.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.field not in FIELDS:
        raise StoryError("(Unknown field.)")
    if params.companion not in COMPANIONS:
        raise StoryError("(Unknown companion.)")
    if params.rune not in RUNES:
        raise StoryError("(Unknown rune.)")
    child = Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        role=params.child_role,
        traits=["young", "hopeful"],
    )
    world = tell(FIELDS[params.field], COMPANIONS[params.companion], RUNES[params.rune], child)
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
        print(asp_program(show="#show valid/3.\n#show eligible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            header = f"### {sample.params.child_name} and the flower field"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
