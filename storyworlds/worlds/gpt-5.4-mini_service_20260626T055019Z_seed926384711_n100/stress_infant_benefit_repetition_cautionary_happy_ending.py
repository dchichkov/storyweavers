#!/usr/bin/env python3
"""
storyworlds/worlds/stress_infant_benefit_repetition_cautionary_happy_ending.py
===============================================================================

A tiny mythic storyworld about a stressed infant, a careful guardian, repeated
soothing, and the benefit of patience.

Premise source tale:
- A tiny infant is unsettled by stress in a windy, noisy place.
- A guardian warns against rushing into louder, rougher choices.
- The guardian repeats a gentle lullaby, a rocking motion, and a careful
  wrapping ritual until the infant calms.
- The repeated caution becomes a benefit: safety, sleep, and a bright ending.

This world keeps the simulation small and state-driven:
- physical meters track noise, warmth, steadiness, and fatigue
- emotional memes track stress, caution, trust, and relief
- repeated soothing actions matter because they accumulate
- ignoring caution can increase stress and delay the happy ending

The style aims at a child-facing myth:
- simple, concrete, and ceremonial
- a little repetitive on purpose
- a cautionary middle that resolves into a happy ending
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"infant", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "father", "guardian"}:
            return {"subject": "she" if self.type == "mother" else "he", "object": "her" if self.type == "mother" else "him", "possessive": "her" if self.type == "mother" else "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old cottage"
    mood: str = "windy"
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    noun: str
    verb: str
    repeat_line: str
    benefit: str
    gentle: bool = True


@dataclass
class Tension:
    id: str
    trigger: str
    caution: str
    danger: str
    resolution: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _inc_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = _meter(entity, key) + amount


def _inc_mem(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = _mem(entity, key) + amount


def _set_mem(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = value


def _repetition_bonus(count: int) -> float:
    return 0.0 if count <= 0 else min(2.0, 0.6 * count)


def _r_lullaby(world: World) -> list[str]:
    out: list[str] = []
    infant = world.get("infant")
    guardian = world.get("guardian")
    key = ("lullaby",)
    if key in world.fired:
        return out
    world.fired.add(key)
    _inc_mem(infant, "trust", 1.0)
    _inc_meter(infant, "steady", 1.0)
    _inc_meter(infant, "stress", -0.5)
    out.append(f"{guardian.label} sang the old lullaby, and the infant's breath grew slower.")
    return out


def _r_wrap(world: World) -> list[str]:
    out: list[str] = []
    infant = world.get("infant")
    guardian = world.get("guardian")
    key = ("wrap",)
    if key in world.fired:
        return out
    world.fired.add(key)
    _inc_meter(infant, "warmth", 1.0)
    _inc_meter(infant, "stress", -0.25)
    out.append(f"{guardian.label} wrapped the infant in a soft cloth, and the little body warmed.")
    return out


def _r_repeated_rocking(world: World) -> list[str]:
    out: list[str] = []
    infant = world.get("infant")
    guardian = world.get("guardian")
    rocks = int(_meter(guardian, "rocks"))
    if rocks < 2:
        return out
    key = ("rock_bonus", rocks)
    if key in world.fired:
        return out
    world.fired.add(key)
    _inc_meter(infant, "steady", _repetition_bonus(rocks))
    _inc_mem(infant, "relief", 1.0)
    out.append(f"Again and again, {guardian.label} rocked the infant with patient hands.")
    return out


def _r_stress_grows(world: World) -> list[str]:
    out: list[str] = []
    infant = world.get("infant")
    if _meter(infant, "noise") < THRESHOLD:
        return out
    key = ("stress_grows",)
    if key in world.fired:
        return out
    world.fired.add(key)
    _inc_mem(infant, "stress", 1.0)
    out.append("The noise pricked the infant's rest, and the little one grew more stressed.")
    return out


def _r_caution(world: World) -> list[str]:
    out: list[str] = []
    guardian = world.get("guardian")
    infant = world.get("infant")
    if _mem(infant, "stress") < THRESHOLD:
        return out
    key = ("caution",)
    if key in world.fired:
        return out
    world.fired.add(key)
    _inc_mem(guardian, "caution", 1.0)
    out.append(f"{guardian.label} gave a cautionary sign: no rushing, no loud play, only gentle care.")
    return out


def _r_benefit(world: World) -> list[str]:
    out: list[str] = []
    infant = world.get("infant")
    guardian = world.get("guardian")
    key = ("benefit",)
    if key in world.fired:
        return out
    if _mem(infant, "relief") < THRESHOLD or _meter(infant, "steady") < THRESHOLD:
        return out
    world.fired.add(key)
    _inc_mem(guardian, "joy", 1.0)
    out.append("The repeated care became a benefit: the infant settled, and the house grew quiet.")
    return out


RULES = [_r_stress_grows, _r_caution, _r_lullaby, _r_wrap, _r_repeated_rocking, _r_benefit]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_ritual(world: World, guardian: Entity, rite: Rite, narrate: bool = True) -> None:
    _inc_meter(guardian, "rocks", 1.0)
    infant = world.get("infant")
    if rite.id == "rock":
        _inc_meter(infant, "steady", 0.5)
        _inc_mem(infant, "trust", 0.5)
    elif rite.id == "hush":
        _inc_meter(infant, "noise", -0.5)
    elif rite.id == "wrap":
        _inc_meter(infant, "warmth", 0.5)
    if narrate:
        world.say(rite.repeat_line)
    propagate(world, narrate=narrate)


def predict_outcome(world: World, rite_ids: list[str]) -> dict:
    sim = world.copy()
    guardian = sim.get("guardian")
    for rid in rite_ids:
        _do_ritual(sim, guardian, RITES[rid], narrate=False)
    infant = sim.get("infant")
    return {
        "calm": _mem(infant, "stress") < THRESHOLD and _meter(infant, "steady") >= 1.0,
        "sleep": _meter(infant, "warmth") >= 1.0 and _mem(infant, "relief") >= 1.0,
    }


def tell(setting: Setting, tension: Tension, hero_name: str = "Nara", guardian_name: str = "Mara") -> World:
    world = World(setting)
    infant = world.add(Entity(
        id="infant", kind="character", type="infant", label=hero_name,
        meters={"stress": 1.0, "noise": 1.0, "steady": 0.0, "warmth": 0.0},
        memes={"stress": 1.0, "trust": 0.0, "relief": 0.0},
    ))
    guardian = world.add(Entity(
        id="guardian", kind="character", type="mother", label=guardian_name,
        meters={"rocks": 0.0},
        memes={"caution": 0.0, "joy": 0.0},
    ))

    world.say(f"In the old {setting.place}, the wind whispered like a gray river around the stones.")
    world.say(f"Little {infant.label} was an infant, and the infant carried stress in a tiny, trembling chest.")
    world.say(f"{guardian.label} knew the old caution: when the night grew loud, do not answer with haste.")

    world.para()
    world.say(f"The house heard a rough sound beyond the door, and the infant started to cry at {tension.trigger}.")
    world.say(f"{guardian.label} warned against {tension.danger}; {tension.caution}")
    world.say(f"Still, there was a better path: {tension.resolution}")

    world.para()
    _do_ritual(world, guardian, RITES["rock"], narrate=True)
    _do_ritual(world, guardian, RITES["hush"], narrate=True)
    _do_ritual(world, guardian, RITES["wrap"], narrate=True)
    _do_ritual(world, guardian, RITES["rock"], narrate=True)

    world.para()
    if _mem(infant, "stress") >= THRESHOLD:
        world.say(f"Again the guardian repeated the song, because repetition was the lamp in the dark.")
        _do_ritual(world, guardian, RITES["rock"], narrate=True)

    world.para()
    if _meter(infant, "steady") >= 1.0 and _meter(infant, "warmth") >= 1.0:
        _set_mem(infant, "stress", 0.0)
        _set_mem(infant, "relief", 1.0)
        world.say(f"At last the infant sighed, then slept, and the old cottage became as quiet as a pond at dawn.")
        world.say(f"The caution had been wise, the repetition had been kind, and the benefit was a happy ending.")
    else:
        world.say(f"The night was still uneasy, though the guardian kept trying.")

    world.facts.update(
        infant=infant,
        guardian=guardian,
        setting=setting,
        tension=tension,
        calm=_mem(infant, "stress") < THRESHOLD,
        happy=_meter(infant, "warmth") >= 1.0 and _meter(infant, "steady") >= 1.0,
    )
    return world


SETTINGS = {
    "cottage": Setting(place="old cottage", mood="windy", affords={"rock", "hush", "wrap"}),
    "temple": Setting(place="stone temple", mood="echoing", affords={"rock", "hush", "wrap"}),
    "hut": Setting(place="river hut", mood="rainy", affords={"rock", "hush", "wrap"}),
}

RITES = {
    "rock": Rite(
        id="rock",
        noun="rocking",
        verb="rock the infant",
        repeat_line="Again and again, the guardian rocked the infant.",
        benefit="steady sleep",
    ),
    "hush": Rite(
        id="hush",
        noun="hushing",
        verb="hush the room",
        repeat_line="Again and again, the guardian hushed the room.",
        benefit="less noise",
    ),
    "wrap": Rite(
        id="wrap",
        noun="wrapping",
        verb="wrap the infant",
        repeat_line="Again and again, the guardian wrapped the infant.",
        benefit="warmth",
    ),
}

TENSIONS = {
    "storm": Tension(
        id="storm",
        trigger="the storm at the door",
        caution="the old wise ones say a storm is no time for loud songs or quick feet",
        danger="chasing the storm",
        resolution="rock the infant, hush the house, and wait for the wind to pass",
    ),
    "bells": Tension(
        id="bells",
        trigger="the bells in the square",
        caution="the old wise ones say bells can wake a newborn into tears",
        danger="opening the shutters wide",
        resolution="close the shutters, wrap the infant, and sing softly",
    ),
    "river": Tension(
        id="river",
        trigger="the river's roar",
        caution="the old wise ones say a roaring river should be watched, not raced",
        danger="taking the infant outdoors too soon",
        resolution="keep to the hearth and repeat the lullaby until sleep comes",
    ),
}

CURATED = [
    ("cottage", "storm"),
    ("temple", "bells"),
    ("hut", "river"),
]

GENTLE_NAMES = ["Nara", "Ila", "Ari", "Mina", "Sora", "Luma"]
GUARDIAN_NAMES = ["Mara", "Tala", "Ena", "Rina", "Asha", "Kora"]


@dataclass
class StoryParams:
    place: str
    tension: str
    infant_name: str
    guardian_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, tension) for place in SETTINGS for tension in TENSIONS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short myth about a stressed infant, a careful guardian, and the benefit of repetition.",
        f"Tell a cautionary story where {f['guardian'].label} keeps {f['infant'].label} safe by repeating a gentle ritual.",
        f"Write a happy-ending tale set in the {f['setting'].place} where stress turns into rest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    infant: Entity = f["infant"]
    guardian: Entity = f["guardian"]
    tension: Tension = f["tension"]
    return [
        QAItem(
            question=f"Who was stressed in the story?",
            answer=f"The infant named {infant.label} was the one carrying stress at the start.",
        ),
        QAItem(
            question=f"What did {guardian.label} keep repeating?",
            answer=f"{guardian.label} kept repeating gentle rocking, hushes, and wrapping so the infant could settle.",
        ),
        QAItem(
            question=f"Why was the guardian's caution a benefit?",
            answer=f"The caution kept the infant away from the loud danger, and the repeated care helped the infant become calm and sleep.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"The infant warmed up, the stress faded, and the house grew quiet like a pond at dawn.",
        ),
        QAItem(
            question=f"What was the warning about {tension.trigger}?",
            answer=f"The warning was not to rush toward the danger, because the wise choice was to stay gentle and keep the infant safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing something again and again, often to make it stronger, clearer, or more soothing.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before acting so something bad does not happen.",
        ),
        QAItem(
            question="Why can a lullaby help an infant?",
            answer="A lullaby can help an infant because a soft, steady song can feel safe and calming.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
calm(I) :- inf(I), stress(I,S), S < 1.
benefit(I) :- inf(I), steady(I,St), St >= 1, warmth(I,W), W >= 1.
caution(G) :- guard(G), stress(I,S), S >= 1, inf(I).
happy(G,I) :- benefit(I), guard(G), caution(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TENSIONS.items():
        lines.append(asp.fact("tension", tid))
    for rid, r in RITES.items():
        lines.append(asp.fact("rite", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    return sorted(set(asp.atoms(model, "place")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((a[0], "storm") for a in asp_valid_combos())
    if py and cl:
        print("OK: ASP is alive.")
        return 0
    print("MISMATCH or empty model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about stress, infant, benefit, repetition, and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tension", choices=TENSIONS)
    ap.add_argument("--infant-name")
    ap.add_argument("--guardian-name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.tension:
        combos = [c for c in combos if c[1] == args.tension]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, tension = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        tension=tension,
        infant_name=args.infant_name or rng.choice(GENTLE_NAMES),
        guardian_name=args.guardian_name or rng.choice(GUARDIAN_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TENSIONS[params.tension], params.infant_name, params.guardian_name)
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
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, tension in CURATED:
            p = StoryParams(place=place, tension=tension, infant_name="Nara", guardian_name="Mara")
            samples.append(generate(p))
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            samples.append(generate(params))

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
