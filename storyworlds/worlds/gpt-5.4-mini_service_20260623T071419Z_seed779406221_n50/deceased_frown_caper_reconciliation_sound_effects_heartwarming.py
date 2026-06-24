#!/usr/bin/env python3
"""
storyworlds/worlds/deceased_frown_caper_reconciliation_sound_effects_heartwarming.py
====================================================================================

A tiny heartwarming storyworld about a small caper, a frown, and a gentle
reconciliation after a loss. The world centers on a child who misses someone
deceased, a helper who tries to help in the wrong way, and a final turn that
uses sound effects to repair hurt feelings.

The seed-image:
A child, a grown-up helper, and a small caper in a cozy place. The child is
frowning because they miss a deceased loved one. A cheerful sound effect helps
them work together, and the story ends with reconciliation.

This file follows the Storyweavers storyworld contract:
- stdlib-only standalone script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py only in ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- valid_combos, Python reasonableness gate, inline ASP twin, --verify, --show-asp
- state-driven prose with typed entities, physical meters, emotional memes
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    cozy: str
    sounds: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    at_risk: str
    triggers_frown: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundCue:
    id: str
    label: str
    onomatopoeia: str
    meaning: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


def _init_meters() -> dict[str, float]:
    return {"frown": 0.0, "warmth": 0.0, "miss": 0.0, "joy": 0.0, "reconcile": 0.0}


def _set_defaults(ent: Entity) -> Entity:
    for k, v in _init_meters().items():
        ent.meters.setdefault(k, v)
    for k in ("sadness", "hope", "regret", "care", "comfort"):
        ent.memes.setdefault(k, 0.0)
    return ent


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for loss in LOST_THINGS:
            for cue in SOUND_CUES:
                if reasonableness_ok(place, loss, cue):
                    combos.append((place, loss, cue))
    return combos


@dataclass
class StoryParams:
    place: str
    loss: str
    cue: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", cozy="warm and bright", sounds=["clink", "hum"], tags={"cozy"}),
    "library": Place(id="library", label="the library corner", cozy="quiet and soft", sounds=["shh", "rustle"], tags={"cozy"}),
    "porch": Place(id="porch", label="the porch", cozy="sunny and breezy", sounds=["creak", "tap"], tags={"cozy"}),
}

LOST_THINGS = {
    "photo": LostThing(id="photo", label="old photo", phrase="a small old photo", at_risk="drawer", tags={"memory", "deceased"}),
    "scarf": LostThing(id="scarf", label="red scarf", phrase="a soft red scarf", at_risk="chair", tags={"memory"}),
    "button": LostThing(id="button", label="blue button", phrase="a shiny blue button", at_risk="rug", tags={"memory"}),
}

SOUND_CUES = {
    "giggle": SoundCue(id="giggle", label="giggle", onomatopoeia="hee-hee", meaning="a tiny laugh that eases the room", helps="made the frown crack open", tags={"sound"}),
    "chime": SoundCue(id="chime", label="chime", onomatopoeia="ding-ding", meaning="a clear, bright bell sound", helps="helped everyone breathe again", tags={"sound"}),
    "tap": SoundCue(id="tap", label="tap-tap", onomatopoeia="tap-tap", meaning="a gentle rhythm on the table", helps="turned the caper into a game", tags={"sound"}),
}

GIRL_NAMES = ["Maya", "Nina", "Lina", "Rose", "Ivy", "Ada"]
BOY_NAMES = ["Ben", "Owen", "Theo", "Noah", "Milo", "Eli"]


def reasonableness_ok(place: Place, loss: LostThing, cue: SoundCue) -> bool:
    return "cozy" in place.tags and "sound" in cue.tags and "memory" in loss.tags


def explanation_for_invalid(place: Place, loss: LostThing, cue: SoundCue) -> str:
    return (
        f"(No story: this setting, lost item, and sound cue do not make a gentle caper. "
        f"Try a cozy place, a memory-linked object, and a soft sound effect.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming caper with reconciliation and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--loss", choices=LOST_THINGS)
    ap.add_argument("--cue", choices=SOUND_CUES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.place and args.loss and args.cue:
        if not reasonableness_ok(PLACES[args.place], LOST_THINGS[args.loss], SOUND_CUES[args.cue]):
            raise StoryError(explanation_for_invalid(PLACES[args.place], LOST_THINGS[args.loss], SOUND_CUES[args.cue]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.loss is None or c[1] == args.loss)
              and (args.cue is None or c[2] == args.cue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, loss, cue = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, loss=loss, cue=cue, child_name=child_name, child_gender=child_gender, helper_name=helper_name, helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = _set_defaults(world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name)))
    helper = _set_defaults(world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name)))
    loss = _set_defaults(world.add(Entity(id="loss", kind="thing", type="thing", label=LOST_THINGS[params.loss].label, phrase=LOST_THINGS[params.loss].phrase, tags=set(LOST_THINGS[params.loss].tags))))
    cue = SOUND_CUES[params.cue]

    child.memes["sadness"] = 2.0
    child.meters["frown"] = 1.0
    child.meters["miss"] = 1.0
    helper.memes["care"] = 1.0

    world.say(f"{child.label} was frowning in {world.place.label}, because {child.pronoun('possessive')} heart still missed {LOST_THINGS[params.loss].phrase}.")
    world.say(f"The room felt {world.place.cozy}, but the little frown stayed anyway.")
    world.para()

    child.memes["hope"] += 1.0
    world.say(f"{helper.label} noticed the frown and tiptoed closer with a gentle smile.")
    world.say(f'"What if we make a tiny caper?" {helper.label} asked. "A search, a clue, and a sound effect."')
    world.para()

    child.memes["regret"] += 1.0
    world.say(f"{child.label} led the search to the {LOST_THINGS[params.loss].at_risk}, where the missing thing usually hid.")
    world.say(f'Then came the clue: "{cue.onomatopoeia}!" The sound effect bounced softly across the room.')
    child.meters["frown"] = 0.0
    child.meters["joy"] += 1.0
    helper.meters["warmth"] += 1.0
    world.say(f"The little sound made the frown crack open, and the caper turned into a game.")
    world.para()

    child.meters["reconcile"] += 1.0
    helper.meters["reconcile"] += 1.0
    child.memes["comfort"] += 1.0
    world.say(f"{child.label} found the old {loss.label} and held it close.")
    world.say(f"Together they whispered about the deceased loved one who had once cherished it, and the memory felt tender instead of sharp.")
    world.say(f'{helper.label} said, "We can miss someone and still smile together."')
    world.say(f"The two of them sat side by side, listening to the soft {cue.label} of the room and feeling better.")
    world.say(f"By the end, the child was no longer frowning; {child.label} was hugging the keepsake, and the helper was hugging back.")
    world.say(f"It was a small caper, but it ended with a warm reconciliation and a happy, quiet hush.")

    world.facts.update(
        child=child,
        helper=helper,
        loss=loss,
        cue=cue,
        place=world.place,
        reconciled=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a 3-to-5-year-old about {f["child"].label}, who is frowning because they miss someone deceased, and a gentle caper that leads to reconciliation.',
        f"Tell a cozy story in {f['place'].label} where {f['helper'].label} uses a soft sound effect to help {f['child'].label} stop frowning and feel better.",
        f'Write a simple story that includes a little caper, a sound effect like "{f["cue"].onomatopoeia}", and an ending where two people reconcile after sadness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    loss = f["loss"]
    cue = f["cue"]
    place = f["place"]
    return [
        QAItem(
            question=f"Why was {child.label} frowning at {place.label}?",
            answer=f"{child.label} was frowning because {child.pronoun('possessive')} heart missed {loss.phrase}, and the feeling of loss was still fresh.",
        ),
        QAItem(
            question=f"What did {helper.label} do to help {child.label} during the caper?",
            answer=f"{helper.label} started a gentle caper, stayed close, and used a soft sound effect so the search felt playful instead of sad.",
        ),
        QAItem(
            question=f"What sound did the story use when the caper reached the clue?",
            answer=f"It used {cue.onomatopoeia}. That little sound helped the room feel lighter and gave both of them a new way to smile.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{child.label} stopped frowning, found comfort in the keepsake, and reconciled with {helper.label}. They ended the story sitting together, feeling warm and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who felt upset or apart come back together kindly. They may talk, forgive, and feel close again.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a small sound that helps tell a story, like a tap, a ding, or a giggle. It can make a scene feel playful or gentle.",
        ),
        QAItem(
            question="Why do people keep keepsakes?",
            answer="People keep keepsakes because they remind them of someone they love. A keepsake can help a memory feel warm and close.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: label={e.label!r} meters={e.meters} memes={e.memes} tags={sorted(e.tags)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", loss="photo", cue="chime", child_name="Maya", child_gender="girl", helper_name="Ben", helper_gender="boy"),
    StoryParams(place="library", loss="scarf", cue="giggle", child_name="Noah", child_gender="boy", helper_name="Ivy", helper_gender="girl"),
    StoryParams(place="porch", loss="button", cue="tap", child_name="Lina", child_gender="girl", helper_name="Eli", helper_gender="boy"),
]


ASP_RULES = r"""
valid(P,L,C) :- place(P), loss(L), cue(C), cozy(P), memory_loss(L), sound_cue(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("cozy", pid))
    for lid in LOST_THINGS:
        lines.append(asp.fact("loss", lid))
        lines.append(asp.fact("memory_loss", lid))
    for cid in SOUND_CUES:
        lines.append(asp.fact("cue", cid))
        lines.append(asp.fact("sound_cue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH")
        if py - cl:
            print("only in python:", sorted(py - cl))
        if cl - py:
            print("only in clingo:", sorted(cl - py))
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("Smoke test failed: empty story")
        return 1
    print(f"OK: {len(py)} combos; smoke story generated.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(" ".join(t) for t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
