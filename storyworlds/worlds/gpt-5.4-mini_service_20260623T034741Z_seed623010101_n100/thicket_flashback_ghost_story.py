#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/thicket_flashback_ghost_story.py
============================================================================================================

A small standalone storyworld in a ghost-story style with a flashback beat.

Premise:
A child hears a soft haunting from a thicket behind an old fence and learns it
is not a scary ghost at all, but a lost lantern memory tied to a kind past
moment. The story uses a flashback to reveal why the lantern matters, then
resolves with a gentle act that changes the world state.

The world models:
- a child, a guide/caretaker, a thicket, a small lost object, and a ghostly glow
- physical meters: wetness, rust, tangledness, glow, distance, foundness
- emotional memes: fear, curiosity, grief, relief, care, bravery, longing
- a flashback that changes meaning by revealing a past promise
- a resolution where the child retrieves the object and the ghostly presence
  turns warm rather than frightening

This file is intentionally self-contained and uses only the standard library
for the prose engine. The shared results containers are imported eagerly from
storyworlds/results.py, and ASP helpers are imported lazily inside ASP helpers.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    caretaker: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoors: bool = False
    mood: str = "quiet"


@dataclass
class Ghost:
    id: str
    voice: str
    glow_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    ghost: str
    lost: str
    child: str
    gender: str
    guide: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            items = rule.apply(world)
            if items:
                changed = True
                out.extend(items)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_rust(world: World) -> list[str]:
    out: list[str] = []
    lantern = world.get("lantern")
    if lantern.meters.get("wet", 0) >= THRESHOLD and lantern.meters.get("rust", 0) < THRESHOLD:
        sig = ("rust",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        lantern.meters["rust"] = 1.0
        out.append("The little lantern began to rust in the damp dark.")
    return out


def _r_glow(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.meters.get("glow", 0) >= THRESHOLD and world.get("child").memes.get("fear", 0) < THRESHOLD:
        sig = ("glow",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        out.append("The glow no longer felt cold; it turned soft and familiar.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    lantern = world.get("lantern")
    if lantern.meters.get("found", 0) >= THRESHOLD and child.memes.get("fear", 0) >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["fear"] = 0.0
        child.memes["relief"] = 1.0
        out.append("The child felt relief spill through the chest like warm tea.")
    return out


RULES = [Rule("rust", _r_rust), Rule("glow", _r_glow), Rule("relief", _r_relief)]


def flashback(world: World, child: Entity, guide: Entity, lantern: Entity) -> None:
    world.say(
        f"Long ago, before the thicket grew wild, {child.id} and {guide.id} had "
        f"shared a careful walk home with that lantern. {guide.id} had promised "
        f"to keep the path bright until the child reached the gate."
    )
    child.memes["longing"] = child.memes.get("longing", 0) + 1
    lantern.meters["found"] = lantern.meters.get("found", 0) + 1


def make_world(setting: Setting, ghost: Ghost, lost: LostThing,
               child_name: str, gender: str, guide_role: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=gender, label=child_name,
                             role="child", meters={"distance": 0.0}, memes={
                                 "fear": 0.0, "curiosity": 1.0, "bravery": 0.0,
                                 "relief": 0.0, "longing": 0.0
                             }))
    guide = world.add(Entity(id="guide", kind="character", type=guide_role, label="the guide",
                             role="guide", meters={"distance": 0.0}, memes={
                                 "care": 1.0, "fear": 0.0, "relief": 0.0
                             }))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern",
                               phrase=lost.phrase, role="lost",
                               meters={"wet": 0.0, "rust": 0.0, "found": 0.0},
                               tags=set(lost.tags)))
    ghost_ent = world.add(Entity(id="ghost", type="thing", label="ghost glow",
                                 phrase=ghost.voice, role="ghost",
                                 meters={"glow": 0.0}, memes={"grief": 1.0, "kindness": 0.0},
                                 tags=set(ghost.tags)))
    world.facts.update(child=child, guide=guide, lantern=lantern, ghost=ghost_ent,
                       setting=setting, lost=lost, ghost_cfg=ghost)
    return world


def tell(setting: Setting, ghost: Ghost, lost: LostThing,
         child_name: str = "Mara", gender: str = "girl", guide_role: str = "mother") -> World:
    world = make_world(setting, ghost, lost, child_name, gender, guide_role)
    child = world.get("child")
    guide = world.get("guide")
    lantern = world.get("lantern")
    ghost_ent = world.get("ghost")

    world.say(
        f"At {setting.place}, the night was so quiet that even the trees seemed "
        f"to listen. Behind the fence, a thicket shivered, and a small ghostly glow "
        f"wavered among the branches."
    )
    world.say(
        f"{child.id} felt a pinch of fear, but also curiosity. The glow looked like "
        f"it knew a secret."
    )
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    ghost_ent.meters["glow"] += 1

    world.para()
    world.say(
        f"{guide.id} lifted a hand and said the glow was not a wicked thing. "
        f"It was a lost memory, stuck in the thicket where the wet leaves held it."
    )
    world.say(
        f"Then came a flashback: {guide.id} remembered the lantern from a safer "
        f"evening, when its light had helped {child.id} find the gate home."
    )
    flashback(world, child, guide, lantern)

    world.para()
    world.say(
        f"{child.id} stepped closer, parting the branches of the thicket with slow, "
        f"careful fingers. There, half-hidden in moss, was the lantern."
    )
    lantern.meters["wet"] += 1
    lantern.meters["distance"] = 0.0
    propagate(world, narrate=True)

    world.say(
        f"{child.id} lifted it free, wiped away the mud, and held it up to the pale "
        f"moon. The ghostly glow settled into a gentle shine."
    )
    ghost_ent.memes["grief"] = 0.0
    ghost_ent.memes["kindness"] = 1.0
    ghost_ent.meters["glow"] += 1

    world.para()
    world.say(
        f"At last, the thicket was only a thicket again, and the lantern was warm "
        f"in {child.id}'s hands. The ghost did not vanish; it simply looked happy "
        f"to be remembered."
    )
    world.say(
        f"{child.id} and {guide.id} walked home with the lantern lit, and the dark "
        f"path behind them felt less like a haunting and more like a promise kept."
    )

    world.facts.update(resolved=True)
    return world


SETTINGS = {
    "gate": Setting(place="the old garden gate"),
    "yard": Setting(place="the back yard"),
    "path": Setting(place="the stone path"),
}

GHOSTS = {
    "lantern_spirit": Ghost(id="lantern_spirit", voice="a thin glow that knew the way home",
                            glow_word="glow", tags={"ghost", "lantern", "memory"}),
    "kind_echo": Ghost(id="kind_echo", voice="a whisper that remembered a promise",
                       glow_word="whisper", tags={"ghost", "memory"}),
}

LOST_THINGS = {
    "lantern": LostThing(id="lantern", label="lantern", phrase="a brass lantern",
                         risk="wet leaves", tags={"lantern", "wet", "memory"}),
    "key": LostThing(id="key", label="key", phrase="a small iron key",
                     risk="mud", tags={"key", "memory"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for g in GHOSTS:
            for l in LOST_THINGS:
                combos.append((s, g, l))
    return combos


def _gather(params: StoryParams) -> tuple[Setting, Ghost, LostThing]:
    if params.setting not in SETTINGS:
        raise StoryError("unknown setting")
    if params.ghost not in GHOSTS:
        raise StoryError("unknown ghost")
    if params.lost not in LOST_THINGS:
        raise StoryError("unknown lost thing")
    return SETTINGS[params.setting], GHOSTS[params.ghost], LOST_THINGS[params.lost]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a young child that includes the word "thicket" and a flashback about a lost lantern.',
        f"Tell a quiet spooky story where {f['child'].label} sees a glow in the thicket, remembers an old promise, and finds the lantern.",
        "Write a child-facing ghost story that starts eerie, flashes back to a kinder memory, and ends with the dark place feeling safe."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    guide: Entity = f["guide"]
    lantern: Entity = f["lantern"]
    qas = [
        QAItem(
            question=f"Why did {child.label} feel scared when the glow appeared in the thicket?",
            answer=f"{child.label} felt scared because the thicket was dark and the glow looked like a ghost at first. But the fear was mixed with curiosity, so {child.label} kept looking instead of running away."
        ),
        QAItem(
            question="What did the flashback show about the lantern?",
            answer=f"The flashback showed that {guide.label_word} had carried the lantern on an earlier walk home and promised to keep the path bright. That memory explained why the lantern mattered so much."
        ),
        QAItem(
            question=f"How did {child.label} change the ending of the story?",
            answer=f"{child.label} pushed through the thicket, found the lantern, and wiped away the mud. That made the ghostly glow turn gentle, so the ending felt safe instead of frightening."
        ),
    ]
    if f.get("resolved"):
        qas.append(
            QAItem(
                question=f"What was the last thing {child.label} and {guide.label_word} did with the lantern?",
                answer=f"They walked home with the lantern lit, and the path behind them no longer felt haunted. The little light proved that the story had changed from fear to comfort."
            )
        )
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    lost: LostThing = f["lost"]
    ghost: Ghost = f["ghost_cfg"]
    qas = [
        QAItem(
            question="What is a thicket?",
            answer="A thicket is a thick tangle of bushes or branches. It can look dark and crowded, like a little wall of leaves."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly goes back to something that happened earlier. It helps explain why a thing matters now."
        ),
        QAItem(
            question="Why can a lantern be useful at night?",
            answer="A lantern gives a steady light, so people can see a path or find something in the dark. It helps a place feel less scary."
        ),
    ]
    if "ghost" in ghost.tags or "memory" in ghost.tags:
        qas.append(QAItem(
            question="Why might a ghost in a story not be scary?",
            answer="Sometimes a ghost is just a sign of a memory, a promise, or a feeling that has been left behind. Then the ghost can seem gentle instead of mean."
        ))
    return qas


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        em = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if em:
            bits.append(f"memes={em}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world with a thicket and a flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father"])
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
              and (args.ghost is None or c[1] == args.ghost)
              and (args.lost is None or c[2] == args.lost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ghost, lost = rng.choice(sorted(combos))
    child = args.child or rng.choice(["Mina", "Ivy", "Nora", "Eli", "Tess", "Finn"])
    gender = args.gender or rng.choice(["girl", "boy"])
    guide = args.guide or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, ghost=ghost, lost=lost, child=child, gender=gender, guide=guide)


def generate(params: StoryParams) -> StorySample:
    setting, ghost, lost = _gather(params)
    world = tell(setting, ghost, lost, params.child, params.gender, params.guide)
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


CURATED = [
    StoryParams(setting="gate", ghost="lantern_spirit", lost="lantern", child="Mina", gender="girl", guide="mother"),
    StoryParams(setting="yard", ghost="kind_echo", lost="key", child="Eli", gender="boy", guide="father"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
    for l in LOST_THINGS:
        lines.append(asp.fact("lost", l))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,G,L) :- setting(S), ghost(G), lost(L).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP valid-combos:")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if ok:
        print(f"OK: ASP parity and smoke test passed ({len(py)} combos).")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
