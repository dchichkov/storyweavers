#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pylon_motive_semolina_magic_dialogue_bedtime_story.py
=====================================================================================

A small bedtime-story world about a child, a glowing pylon, a bowl of semolina,
and a puzzled motive that is softened by a little magic and a little dialogue.

The premise is simple:
- someone hears a night-time worry,
- a magical pylon responds,
- semolina becomes a calming, practical comfort,
- the characters talk through the worry and end the night safely.

This file is standalone and follows the Storyweavers storyworld contract.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
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
class Setting:
    id: str
    place: str
    mood: str


@dataclass
class MagicItem:
    id: str
    label: str
    glow: str
    use: str
    warmth: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Motive:
    id: str
    label: str
    concern: str
    softening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SemolinaState:
    id: str
    label: str
    bowl: str
    spoon: str
    warmth: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    pylon = world.entities.get("pylon")
    if not child or not parent or not pylon:
        return out
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("calm", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    parent.memes["calm"] += 1
    pylon.meters["glow"] += 1
    out.append("__calm__")
    return out


def _r_stir(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.entities.get("semolina")
    child = world.entities.get("child")
    if not bowl or not child:
        return out
    if child.memes["calm"] < THRESHOLD:
        return out
    sig = ("stir", bowl.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["steam"] += 1
    out.append("__steam__")
    return out


CAUSAL_RULES = [
    Rule("calm", "social", _r_calm),
    Rule("stir", "comfort", _r_stir),
]


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


def predict_calm(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["worry"] += 1
    propagate(sim, narrate=False)
    return {
        "calmed": sim.get("child").memes["calm"] >= THRESHOLD,
        "steam": sim.get("semolina").meters["steam"],
    }


def _night_setup(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At bedtime in {setting.place}, {child.id} looked out at the quiet dark "
        f"and listened to the hush of the house."
    )
    world.say(
        f"{parent.label_word.capitalize()} tucked the blanket in and whispered, "
        f'"Tonight feels gentle, doesn\'t it?"'
    )


def _raise_motive(world: World, child: Entity, motive: Motive) -> None:
    child.memes["worry"] += 1
    child.memes["motive"] += 1
    world.say(
        f"But {child.id} still had a small {motive.label} in {child.pronoun('possessive')} chest: "
        f"{motive.concern}."
    )


def _magic_beacon(world: World, child: Entity, pylon: MagicItem) -> None:
    world.say(
        f"{child.id} peeked at the little {pylon.label} by the window. It {pylon.glow} "
        f"whenever a bedtime thought felt too big."
    )
    world.say(f'"Does the {pylon.label} know what I mean?" {child.id} asked.')


def _dialogue_turn(world: World, child: Entity, parent: Entity, motive: Motive) -> None:
    pred = predict_calm(world)
    world.facts["predicted_calm"] = pred["calmed"]
    world.facts["predicted_steam"] = pred["steam"]
    world.say(
        f'"Yes," {parent.id} said softly. "Tell me your worry, and we will listen to it '
        f'together."'
    )
    world.say(
        f'"I keep thinking the {motive.label} will get louder if I close my eyes," '
        f"{child.id} admitted."
    )
    world.say(
        f'"Then let us make it smaller with words," {parent.id} said. '
        f'"Sometimes a worry is only asking to be named."'
    )


def _share_semolina(world: World, child: Entity, parent: Entity, semolina: SemolinaState) -> None:
    child.memes["trust"] += 1
    parent.memes["tenderness"] += 1
    world.say(
        f"Then {parent.id} brought out {semolina.bowl} and stirred in the warm {semolina.label}. "
        f"It smelled like {semolina.warmth} and tasted like a soft promise."
    )
    world.say(
        f'"Would you like a spoonful?" {parent.id} asked. "{semolina.comfort} can help a big thought feel small."'
    )
    world.say(f'{child.id} nodded and took {semolina.spoon} into {child.pronoun("possessive")} hand.')


def _resolve(world: World, child: Entity, parent: Entity, pylon: MagicItem, semolina: SemolinaState) -> None:
    child.memes["worry"] = 0.0
    child.memes["sleepiness"] += 1
    child.memes["safety"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {pylon.label} glowed a little brighter, as if it agreed. The room felt safe, "
        f"and the worry faded like a shadow at dawn."
    )
    world.say(
        f"{child.id} curled up again with a calmer heart, and the spoon rested beside "
        f"the warm bowl as the night went quiet."
    )
    world.say(
        f'"Good night," {parent.id} whispered. "{semolina.comfort} and brave words make a lovely bedtime."'
    )


SETTINGS = {
    "bedroom": Setting(id="bedroom", place="the bedroom", mood="sleepy"),
    "attic": Setting(id="attic", place="the attic room", mood="hushed"),
    "nursery": Setting(id="nursery", place="the nursery", mood="soft"),
}

MAGIC_ITEMS = {
    "pylon": MagicItem(
        id="pylon",
        label="pylon",
        glow="gave off a tiny blue shimmer",
        use="to keep bedtime thoughts from wobbling",
        warmth=2,
        tags={"pylon", "magic"},
    ),
    "lantern": MagicItem(
        id="lantern",
        label="lantern",
        glow="glimmered like a moon on water",
        use="to light the hall",
        warmth=2,
        tags={"magic"},
    ),
}

MOTIVES = {
    "lost": Motive(
        id="lost",
        label="motive",
        concern="the child was afraid a lost toy would stay missing forever",
        softening="naming the lost thing could make it feel found again",
        tags={"motive"},
    ),
    "storm": Motive(
        id="storm",
        label="motive",
        concern="the child thought a storm sound might sneak under the door",
        softening="a careful voice could make the storm sound feel far away",
        tags={"motive"},
    ),
}

SEMOLINA = {
    "plain": SemolinaState(
        id="plain",
        label="semolina",
        bowl="a little blue bowl",
        spoon="a silver spoon",
        warmth="warm milk and butter",
        comfort="a cozy snack",
        tags={"semolina"},
    ),
    "honey": SemolinaState(
        id="honey",
        label="semolina",
        bowl="a yellow bowl",
        spoon="a tiny wooden spoon",
        warmth="honey and cinnamon",
        comfort="a sweet spoonful",
        tags={"semolina"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Max", "Leo"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    setting: str
    magic: str
    motive: str
    semolina: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="bedroom", magic="pylon", motive="lost", semolina="plain",
                child_name="Mia", child_gender="girl", parent_type="mother"),
    StoryParams(setting="nursery", magic="pylon", motive="storm", semolina="honey",
                child_name="Theo", child_gender="boy", parent_type="father"),
    StoryParams(setting="attic", magic="lantern", motive="lost", semolina="honey",
                child_name="Luna", child_gender="girl", parent_type="mother"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MAGIC_ITEMS:
            for motive_id in MOTIVES:
                for sem_id in SEMOLINA:
                    combos.append((sid, mid, motive_id, sem_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld with magic, dialogue, pylon, motive, and semolina.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--semolina", choices=SEMOLINA)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.magic is None or c[1] == args.magic)
              and (args.motive is None or c[2] == args.motive)
              and (args.semolina is None or c[3] == args.semolina)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, magic, motive, semolina = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(setting=setting, magic=magic, motive=motive, semolina=semolina,
                       child_name=name, child_gender=gender, parent_type=parent)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="the parent", role="parent"))
    pylon = world.add(Entity(id="pylon", type="thing", label="pylon"))
    bowl = world.add(Entity(id="semolina", type="thing", label="semolina"))

    magic = MAGIC_ITEMS[params.magic]
    motive = MOTIVES[params.motive]
    semolina = SEMOLINA[params.semolina]

    _night_setup(world, child, parent, world.setting)
    _magic_beacon(world, child, magic)
    world.para()
    _raise_motive(world, child, motive)
    _dialogue_turn(world, child, parent, motive)
    world.para()
    _share_semolina(world, child, parent, semolina)
    _resolve(world, child, parent, magic, semolina)

    world.facts.update(child=child, parent=parent, pylon=magic, motive=motive, semolina=semolina,
                       setting=world.setting, outcome="calmed")
    pylon.meters["glow"] = magic.warmth
    bowl.meters["steam"] = semolina.warmth.count("warm")
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "{f["pylon"].label}", "{f["motive"].label}", and "{f["semolina"].label}".',
        f"Tell a gentle bedtime story where {f['child'].id} has a small {f['motive'].label} and a glowing {f['pylon'].label} helps after a kind conversation.",
        f"Write a short child-friendly story with magic and dialogue, ending with warm {f['semolina'].label} and a calm bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    motive = f["motive"]
    semolina = f["semolina"]
    return [
        QAItem(
            question=f"What was {child.id} feeling?",
            answer=f"{child.id} was carrying a small {motive.label}. It made bedtime feel a little too big until {parent.id} helped name it.",
        ),
        QAItem(
            question="How did the worry get smaller?",
            answer=f"{parent.id} listened carefully and talked with {child.id} in a soft voice. Then the warm semolina gave the room a cozy feeling, so the worry could settle down.",
        ),
        QAItem(
            question=f"What was special about the {f['pylon'].label}?",
            answer=f"The {f['pylon'].label} gave a tiny magical glow. It was not the main fix by itself, but it made the room feel safe enough for the conversation to work.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} calm, a warm bowl of semolina, and a quiet good-night. The child could sleep because the worry had been named and soothed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is semolina?",
            answer="Semolina is a grainy food that can be cooked into a soft, comforting bowl. People often eat it warm.",
        ),
        QAItem(
            question="What does a pylon usually do in real life?",
            answer="A pylon usually holds or supports something. In this storyworld it is magical, so it can glow and help set a calm mood.",
        ),
        QAItem(
            question="Why can a gentle conversation help at bedtime?",
            answer="A gentle conversation can make a worry feel smaller because the child is no longer carrying it alone. Words can help name the feeling and make it easier to rest.",
        ),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
combo(S,M,Mo,Se) :- setting(S), magic(M), motive(Mo), semolina(Se).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MAGIC_ITEMS:
        lines.append(asp.fact("magic", mid))
    for mo in MOTIVES:
        lines.append(asp.fact("motive", mo))
    for se in SEMOLINA:
        lines.append(asp.fact("semolina", se))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/4."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python combo generation.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, magic=None, motive=None, semolina=None, name=None, gender=None, parent=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.magic not in MAGIC_ITEMS:
        raise StoryError(f"Unknown magic item: {params.magic}")
    if params.motive not in MOTIVES:
        raise StoryError(f"Unknown motive: {params.motive}")
    if params.semolina not in SEMOLINA:
        raise StoryError(f"Unknown semolina state: {params.semolina}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        print(asp_program("#show combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
