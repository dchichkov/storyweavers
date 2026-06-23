#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/announce_assign_sharing_myth.py
==============================================================================================================

A standalone storyworld for a tiny mythic sharing domain.

Premise:
- A village prepares a sacred offering or feast.
- Someone must announce the gathering and assign what each person shares.
- If sharing is handled well, the group leaves with full bowls, calm hearts,
  and a visible sign that the gift truly went to everyone.

The model tracks physical meters and emotional memes across a few typed entities,
uses a small forward-chaining causal system, and mirrors the reasonableness gate
with inline ASP rules.

This script is self-contained and stdlib-only apart from the shared result
containers in storyworlds/results.py and the lazy ASP helper in storyworlds/asp.py.
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
    role: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "god"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    kind: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    kind: str
    portions: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    announce_line: str
    assign_line: str
    ending_line: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


PLACES = {
    "hall": Place(id="hall", label="the hall of echoes", kind="hall", supports={"bread", "grain", "honey"}),
    "courtyard": Place(id="courtyard", label="the courtyard of stones", kind="courtyard", supports={"bread", "grain", "honey", "water"}),
    "harbor": Place(id="harbor", label="the harbor steps", kind="harbor", supports={"fish", "bread", "water"}),
    "grove": Place(id="grove", label="the grove under the moon trees", kind="grove", supports={"bread", "honey", "fruit"}),
}

OFFERINGS = {
    "bread": Offering(id="bread", label="loaf", phrase="a warm loaf of bread", kind="bread", portions=4, tags={"bread", "sharing"}),
    "grain": Offering(id="grain", label="bowl of grain", phrase="a bowl of sweet grain", kind="grain", portions=3, tags={"grain", "sharing"}),
    "honey": Offering(id="honey", label="jar of honey", phrase="a jar of golden honey", kind="honey", portions=3, tags={"honey", "sharing"}),
    "water": Offering(id="water", label="jug of water", phrase="a jug of clear water", kind="water", portions=4, tags={"water", "sharing"}),
}

METHODS = {
    "announce_then_assign": Method(
        id="announce_then_assign",
        label="announce then assign",
        announce_line='The elder announced the gift to the people.',
        assign_line='Then the elder assigned each person a fair share.',
        ending_line='Soon every bowl was full, and no one was left waiting.',
        supports={"bread", "grain", "honey", "water"},
        tags={"announce", "assign", "sharing"},
    ),
    "drum_then_share": Method(
        id="drum_then_share",
        label="drum then share",
        announce_line='A drumbeat announced the feast before the first plate moved.',
        assign_line='After that, the keeper assigned the portions one by one.',
        ending_line='The rhythm ended with everyone eating together in peace.',
        supports={"bread", "grain", "honey"},
        tags={"announce", "assign", "sharing"},
    ),
    "torch_then_split": Method(
        id="torch_then_split",
        label="torch then split",
        announce_line='A bright torch announced that the sharing hour had come.',
        assign_line='Next, the watcher assigned the best pieces to the children first.',
        ending_line='The light showed the gift going around until all had enough.',
        supports={"bread", "water", "honey"},
        tags={"announce", "assign", "sharing"},
    ),
    "song_then_measure": Method(
        id="song_then_measure",
        label="song then measure",
        announce_line='A song announced the opening of the gift-bowl.',
        assign_line='Then the singer assigned the portions with a careful measure.',
        ending_line='At the end, the offering lay evenly shared across the cloth.',
        supports={"bread", "grain", "honey", "water"},
        tags={"announce", "assign", "sharing"},
    ),
}

NAMES = ["Ari", "Mira", "Niko", "Sela", "Tava", "Rin", "Pela", "Dorin"]
KINDS = [("girl", "mother"), ("boy", "father"), ("woman", "elder"), ("man", "elder")]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for oid, off in OFFERINGS.items():
            if off.kind in place.supports:
                for mid, method in METHODS.items():
                    if off.kind in method.supports:
                        out.append((pid, oid, mid))
    return out


@dataclass
class StoryParams:
    place: str = ""
    offering: str = ""
    method: str = ""
    announcer_name: str = ""
    announcer_type: str = ""
    announcer_role: str = ""
    helper_name: str = ""
    helper_type: str = ""
    helper_role: str = ""
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic sharing storyworld with announce and assign.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--method", choices=METHODS)
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
              if (args.place is None or c[0] == args.place)
              and (args.offering is None or c[1] == args.offering)
              and (args.method is None or c[2] == args.method)]
    if not combos:
        raise StoryError("No valid mythic sharing combination matches the chosen filters.")
    place, offering, method = rng.choice(sorted(combos))
    a_name = rng.choice(NAMES)
    h_name = rng.choice([n for n in NAMES if n != a_name])
    a_type, a_role = rng.choice(KINDS)
    h_type, h_role = rng.choice(KINDS)
    return StoryParams(
        place=place, offering=offering, method=method,
        announcer_name=a_name, announcer_type=a_type, announcer_role=a_role,
        helper_name=h_name, helper_type=h_type, helper_role=h_role,
    )


def _ensure(d: dict, key: str, default=0.0):
    if key not in d:
        d[key] = default


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.offering not in OFFERINGS:
        raise StoryError("Unknown offering.")
    if params.method not in METHODS:
        raise StoryError("Unknown method.")
    place = PLACES[params.place]
    off = OFFERINGS[params.offering]
    method = METHODS[params.method]
    if off.kind not in place.supports or off.kind not in method.supports:
        raise StoryError("That combination cannot support a true sharing story.")
    world = World(place=place)
    elder = world.add(Entity(id="announcer", kind="character", type=params.announcer_type, label=params.announcer_name, role=params.announcer_role))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, role=params.helper_role))
    bowl = world.add(Entity(id="offering", kind="thing", type=off.kind, label=off.label, phrase=off.phrase, plural=False))
    crowd = world.add(Entity(id="crowd", kind="thing", type="group", label="the gathered people", plural=True))
    _ensure(elder.meters, "warmth")
    _ensure(helper.meters, "warmth")
    _ensure(bowl.meters, "portions", float(off.portions))
    _ensure(elder.memes, "duty")
    _ensure(helper.memes, "trust")
    _ensure(helper.memes, "gratitude")
    world.facts.update(place=place, offering=off, method=method, announcer=elder, helper=helper, bowl=bowl, crowd=crowd, shared=False, announced=False, assigned=False)
    return world


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if world.facts.get("announced") and world.facts.get("assigned") and not world.facts.get("shared"):
        sig = ("share", world.facts["offering"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            off: Entity = world.facts["bowl"]
            off.meters["shared"] = 1
            world.facts["shared"] = True
            world.get("announcer").meters["warmth"] += 1
            world.get("helper").meters["warmth"] += 1
            world.get("helper").memes["gratitude"] += 1
            world.get("announcer").memes["duty"] += 1
            out.append("The gift moved from hand to hand until everyone had a part.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(world: World) -> None:
    elder = world.get("announcer")
    helper = world.get("helper")
    off = world.facts["bowl"]
    method = world.facts["method"]
    world.say(f"In {world.place.label}, {elder.label} and {helper.label} stood before {off.phrase}.")
    world.say(method.announce_line)
    world.facts["announced"] = True
    world.para()
    world.say(method.assign_line)
    world.facts["assigned"] = True
    elder.memes["duty"] += 1
    helper.memes["trust"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(method.ending_line)
    world.say(f"At the last, {off.label} was no longer one thing at all; it had become a shared blessing.")
    world.say(f"{elder.label} smiled, and {helper.label} held the empty bowl like a small moon.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth where someone must announce a sacred sharing and assign the portions in {f["place"].label}.',
        f"Tell a child-friendly myth about {f['announcer'].label} and {f['helper'].label} sharing {f['offering'].phrase} after an announcement.",
        f'Write a gentle mythic story that includes the words "announce" and "assign" and ends with a gift being shared fairly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    elder = f["announcer"]
    helper = f["helper"]
    off = f["offering"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"What did {elder.label} do before the sharing began in {place.label}?",
            answer=f"{elder.label} announced the gift to everyone first. That made the room ready, so the sharing could begin in an orderly way.",
        ),
        QAItem(
            question=f"What did {helper.label} help with after the announcement?",
            answer=f"{helper.label} helped assign the portions one by one. That way, the offering did not stay in one bowl, and each person received a fair part.",
        ),
        QAItem(
            question=f"How did the ending show that {off.label} was shared well?",
            answer=f"The bowl became empty because the gift moved from hand to hand until everyone had a part. The final image shows the offering no longer sitting untouched.",
        ),
    ]
    if f.get("shared"):
        qa.append(QAItem(
            question=f"Why did the people feel calm after the sharing in {place.label}?",
            answer=f"They felt calm because the elder announced the gift and then assigned it fairly. When each person knew what to take, the sharing stayed peaceful and no one was left out.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use or enjoy something. It often feels kind because everyone gets a turn or a fair part.",
        ),
        QAItem(
            question="Why do people announce something before a gathering?",
            answer="People announce something so everyone knows what is happening. A clear announcement helps the group come together without confusion.",
        ),
        QAItem(
            question="What does it mean to assign parts?",
            answer="To assign parts means to give each person a job or a share. This can keep things fair and make a group act together smoothly.",
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
    lines = [f"--- world model state ({world.place.label}) ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: {e.label or e.type} meters={meters} memes={memes}")
    lines.append(f"  facts: announced={world.facts.get('announced')} assigned={world.facts.get('assigned')} shared={world.facts.get('shared')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for oid, o in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        lines.append(asp.fact("kind_of", oid, o.kind))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        for s in sorted(m.supports):
            lines.append(asp.fact("method_supports", mid, s))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,O,M) :- place(P), offering(O), method(M), kind_of(O,K), supports(P,K), method_supports(M,K).
shared(P,O,M) :- valid(P,O,M).
#show valid/3.
#show shared/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok1 = set(asp_valid_combos()) == set(valid_combos())
    if not ok1:
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, offering=None, method=None), random.Random(777)))
        _ = sample.story
        print("OK: ASP parity and normal generation smoke test passed.")
        return 0
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="hall", offering="bread", method="announce_then_assign", announcer_name="Ari", announcer_type="woman", announcer_role="elder", helper_name="Mira", helper_type="girl", helper_role="mother"),
    StoryParams(place="courtyard", offering="grain", method="drum_then_share", announcer_name="Niko", announcer_type="man", announcer_role="elder", helper_name="Sela", helper_type="girl", helper_role="mother"),
    StoryParams(place="harbor", offering="water", method="song_then_measure", announcer_name="Dorin", announcer_type="man", announcer_role="elder", helper_name="Rin", helper_type="boy", helper_role="father"),
    StoryParams(place="grove", offering="honey", method="torch_then_split", announcer_name="Pela", announcer_type="woman", announcer_role="elder", helper_name="Tava", helper_type="girl", helper_role="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid sharing myths:\n")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
