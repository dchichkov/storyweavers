#!/usr/bin/env python3
"""
A standalone storyworld for a bedtime-style suspense tale about procrastinating
before opening a certificate.

The seed idea:
A tired child receives a sealed envelope that holds a special certificate, but
keeps putting off opening it because bedtime feels soft and safe. The suspense
comes from the unopened envelope: Is it a prize? A homework notice? A surprise
from someone kind? A gentle parent or helper nudges the child to open it before
sleep, and the ending proves the certificate was something lovely.

This world models:
- a sleepy child, a parent, and a sealed envelope
- time pressure before bedtime
- the emotional tug between procrastination and curiosity
- the small turn when the child opens the envelope
- a resolving ending image with the certificate revealed
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
    owner: Optional[str] = None
    sealed: bool = False
    opened: bool = False
    hidden_item: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    bedtime: str = "bedtime"
    quiet: bool = True


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    mood: str
    certificate_kind: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    time_left: int = 3

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.time_left = self.time_left
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_time_pressure(world: World) -> list[str]:
    out: list[str] = []
    if world.time_left > 0:
        world.time_left -= 1
        if world.time_left == 0:
            out.append("The room felt even quieter, like bedtime was waiting at the door.")
    return out


def _r_procrastinate(world: World) -> list[str]:
    child = world.get("child")
    envelope = world.get("envelope")
    out: list[str] = []
    if child.memes.get("procrastinate", 0) >= THRESHOLD and not envelope.opened:
        sig = ("procrastinate",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["worry"] = child.memes.get("worry", 0) + 1
        out.append("The child kept delaying, and the sealed envelope seemed to grow more important.")
    return out


def _r_open(world: World) -> list[str]:
    child = world.get("child")
    envelope = world.get("envelope")
    out: list[str] = []
    if child.memes.get("curiosity", 0) >= THRESHOLD and not envelope.opened:
        sig = ("open",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        envelope.opened = True
        child.memes["relief"] = child.memes.get("relief", 0) + 1
        out.append("At last, the envelope opened with a soft whisper.")
    return out


CAUSAL_RULES = [
    Rule("time_pressure", _r_time_pressure),
    Rule("procrastinate", _r_procrastinate),
    Rule("open", _r_open),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="the parent"))
    envelope = world.add(
        Entity(
            id="envelope",
            kind="thing",
            type="envelope",
            label="sealed envelope",
            phrase="a sealed envelope with a ribbon",
            sealed=True,
            hidden_item=params.certificate_kind,
        )
    )
    certificate = world.add(
        Entity(
            id="certificate",
            kind="thing",
            type="certificate",
            label="certificate",
            phrase=f"a shiny {params.certificate_kind} certificate",
        )
    )
    world.facts.update(child=child, parent=parent, envelope=envelope, certificate=certificate)
    return world


def tell(world: World, params: StoryParams) -> World:
    child = world.get("child")
    parent = world.get("parent")
    envelope = world.get("envelope")
    certificate = world.get("certificate")

    child.memes["curiosity"] = 1
    child.memes["procrastinate"] = 1
    child.memes["sleepiness"] = 1

    world.say(
        f"{child.label} was a little {params.child_type} with sleepy eyes and a soft, careful heart."
    )
    world.say(
        f"At {params.place}, {child.pronoun('subject')} found {envelope.phrase} on the night table."
    )
    world.say(
        f"{child.pronoun().capitalize()} knew there was a certificate inside, but {child.pronoun('subject')} kept thinking, "
        f'"I will open it in a minute."'
    )

    world.para()
    world.say(
        f"The clock ticked toward {world.setting.bedtime}, and the room grew still and warm."
    )
    world.say(
        f"{child.label} wanted to procrastinate and leave the envelope unopened, even though curiosity tugged gently at {child.pronoun('possessive')} paws."
    )
    world.say(
        f"{parent.label.capitalize()} sat nearby with a calm smile and said, "
        f'"You do not have to rush, but you should open the certificate before sleep so we can share the surprise."'
    )

    propagate(world, narrate=True)

    if not envelope.opened:
        world.say(
            f"{child.label} hugged the envelope and promised not to hide from it forever."
        )
        child.memes["curiosity"] += 1
        propagate(world, narrate=True)

    world.para()
    if envelope.opened:
        certificate.owner = child.id
        world.say(
            f"Inside was a {params.certificate_kind} certificate with bright letters, and it was for {child.label}."
        )
        world.say(
            f"{child.label} smiled so widely that the sleepiness turned into a cozy glow, and {parent.label} tucked {child.pronoun('object')} in with the certificate beside the pillow."
        )
    else:
        world.say(
            f"The envelope stayed closed, and the room felt unfinished until morning."
        )

    world.facts.update(
        child=child,
        parent=parent,
        envelope=envelope,
        certificate=certificate,
        opened=envelope.opened,
        resolved=envelope.opened,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    certificate = f["certificate"]
    return [
        f"Write a gentle bedtime story about {child.label} who keeps saying {chr(34)}later{chr(34)} before opening a certificate.",
        f"Tell a suspenseful but cozy story where {parent.label} helps a sleepy {child.type} open a certificate at bedtime.",
        f"Write a child-friendly story using the words procrastinate, open, and certificate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    envelope = f["envelope"]
    certificate = f["certificate"]
    out = [
        QAItem(
            question=f"Why did {child.label} keep putting off opening the envelope?",
            answer=(
                f"{child.label} was sleepy and a little nervous about what the sealed envelope might hold, "
                f"so {child.pronoun('subject')} kept procrastinating instead of opening it right away."
            ),
        ),
        QAItem(
            question=f"Who helped {child.label} decide to open the certificate?",
            answer=(
                f"{parent.label} helped by speaking gently and reminding {child.label} that it was safe to open the envelope before sleep."
            ),
        ),
        QAItem(
            question=f"What was inside the sealed envelope?",
            answer=(
                f"Inside was a {certificate.phrase}, which turned out to be a happy surprise for {child.label}."
            ),
        ),
    ]
    if f.get("opened"):
        out.append(
            QAItem(
                question=f"How did {child.label} feel after opening the envelope?",
                answer=(
                    f"{child.label} felt relieved and happy, because the suspense ended and the certificate was something lovely."
                ),
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does procrastinate mean?",
            answer=(
                "To procrastinate means to keep delaying something you should do, even when you know it is time to do it."
            ),
        ),
        QAItem(
            question="What is a certificate?",
            answer=(
                "A certificate is a paper that shows someone earned, learned, or did something special."
            ),
        ),
        QAItem(
            question="Why can opening a sealed envelope feel suspenseful?",
            answer=(
                "It can feel suspenseful because you do not know what is inside yet, so you wonder and wait."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.sealed:
            bits.append("sealed")
        if e.opened:
            bits.append("opened")
        if e.hidden_item:
            bits.append(f"hidden_item={e.hidden_item}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  time_left={world.time_left}")
    return "\n".join(lines)


SETTINGS = {
    "bedroom": Setting(place="the bedroom"),
    "nursery": Setting(place="the nursery"),
    "hallway": Setting(place="the hallway"),
    "cottage": Setting(place="the little cottage"),
}

CERTIFICATE_KINDS = {
    "bravery": "bravery",
    "kindness": "kindness",
    "reading": "reading",
    "sleep": "sleep",
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Sam", "Lily", "Theo"]
CHILD_TYPES = ["girl", "boy"]
PARENTS = ["mother", "father"]
MOODS = ["sleepy", "curious", "hesitant", "shy"]


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    mood: str
    certificate_kind: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about procrastinating before opening a certificate.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child-name", dest="child_name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--parent-type", choices=PARENTS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--certificate-kind", dest="certificate_kind", choices=CERTIFICATE_KINDS)
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
    place = args.place or rng.choice(list(SETTINGS))
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    parent_type = args.parent_type or rng.choice(PARENTS)
    mood = args.mood or rng.choice(MOODS)
    certificate_kind = args.certificate_kind or rng.choice(list(CERTIFICATE_KINDS))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        mood=mood,
        certificate_kind=certificate_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell(world, params)
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


ASP_RULES = r"""
% A story is reasonable when a child procrastinates, the envelope is opened,
% and a certificate is revealed before bedtime ends.

procrastinates(child) :- child_mood(child, sleepy).
wants_open(child) :- sees_envelope(child), curious_about(child).
bedtime_pressure :- setting(bedroom).

good_story(Place, ChildType, ParentType, CertKind) :-
    setting_place(Place),
    child_kind(ChildType),
    parent_kind(ParentType),
    certificate_kind(CertKind).

valid_story(Place, Child, Parent, Cert) :-
    good_story(Place, _, _, _),
    child_name(Child),
    parent_name(Parent),
    certificate_kind(Cert).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting_place", place))
    for c in CHILD_TYPES:
        lines.append(asp.fact("child_kind", c))
    for p in PARENTS:
        lines.append(asp.fact("parent_kind", p))
    for k in CERTIFICATE_KINDS:
        lines.append(asp.fact("certificate_kind", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    python_set = set(
        (place, child, parent, cert)
        for place in SETTINGS
        for child in CHILD_NAMES
        for parent in PARENTS
        for cert in CERTIFICATE_KINDS
    )
    asp_set = set(atoms)
    if asp_set == python_set:
        print(f"OK: clingo parity matches ({len(asp_set)} tuples).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (place, child, parent, cert)
        for place in SETTINGS
        for child in CHILD_NAMES
        for parent in PARENTS
        for cert in CERTIFICATE_KINDS
    ]


def explain_rejection() -> str:
    return "(No story: the requested choices do not fit this bedtime certificate tale.)"


def generate_all() -> list[StoryParams]:
    out = []
    for i, (place, child, parent, cert) in enumerate(valid_combos()[:5]):
        out.append(
            StoryParams(
                place=place,
                child_name=child,
                child_type=CHILD_TYPES[i % 2],
                parent_type=parent,
                mood=MOODS[i % len(MOODS)],
                certificate_kind=cert,
            )
        )
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params_list = generate_all()
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} at {p.place} with a {p.certificate_kind} certificate"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
