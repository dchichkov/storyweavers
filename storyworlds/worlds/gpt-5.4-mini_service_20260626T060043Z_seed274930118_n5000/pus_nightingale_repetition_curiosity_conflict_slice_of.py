#!/usr/bin/env python3
"""
storyworlds/worlds/pus_nightingale_repetition_curiosity_conflict_slice_of.py
============================================================================

A small slice-of-life story world about a child, a healing scrape, repeated
checking, curiosity about the sticky stuff that can appear, and a gentle
conflict that ends in a calm routine.

Seed tale:
---
A child gets a small scrape and keeps peeking at it. The scrape looks odd, and
the child becomes curious about the yellowish pus on the bandage. A parent
worries because the child keeps touching the sore again and again. Outside,
a nightingale sings every evening from the same branch, and the child notices
that the song returns in the same soft pattern. In the end, the child learns to
wash the scrape, leave it alone, and listen to the bird instead of worrying the
wound.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
    place: str
    indoors: bool
    bird_spot: str


@dataclass
class Trouble:
    id: str
    tiny_event: str
    repeated_action: str
    checking_action: str
    risk: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    day_time: str = "evening"

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.day_time = self.day_time
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str
    trouble: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, bird_spot="the open window"),
    "porch": Setting(place="the porch", indoors=False, bird_spot="the pear tree"),
    "garden": Setting(place="the garden", indoors=False, bird_spot="the hedge"),
    "bedroom": Setting(place="the bedroom", indoors=True, bird_spot="the rain gutter"),
}

TROUBLES = {
    "scrape": Trouble(
        id="scrape",
        tiny_event="scraped a knee on the step",
        repeated_action="keep checking the scrape",
        checking_action="peel back the bandage again and again",
        risk="touch the sore too much",
        mess="pus",
        keyword="pus",
        tags={"pus", "wound", "bandage", "repetition"},
    ),
    "scratch": Trouble(
        id="scratch",
        tiny_event="got a scratch from a thorny bush",
        repeated_action="keep poking the scratch",
        checking_action="lift the cloth to look at it again and again",
        risk="make the scratch sore",
        mess="pus",
        keyword="pus",
        tags={"pus", "wound", "bandage", "repetition"},
    ),
}

GIRL_NAMES = ["Maya", "Lena", "Nora", "Ivy", "Zoe", "Mina", "Ava"]
BOY_NAMES = ["Eli", "Theo", "Noah", "Ben", "Sam", "Leo", "Milo"]
TRAITS = ["curious", "quiet", "spirited", "gentle", "thoughtful", "restless"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trouble in TROUBLES:
            combos.append((place, trouble))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world about a child, a small wound, a repeated worry, and a nightingale."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place is not None:
        combos = [c for c in combos if c[0] == args.place]
    if args.trouble is not None:
        combos = [c for c in combos if c[1] == args.trouble]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or select_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trouble=trouble, name=name, gender=gender, parent=parent, trait=trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.trouble not in TROUBLES:
        raise StoryError("Unknown trouble.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    # Every trouble must involve pus, repetition, curiosity, and conflict in this world.
    trouble = TROUBLES[params.trouble]
    if "pus" not in trouble.tags or "repetition" not in trouble.tags:
        raise StoryError("This world requires pus and repetition.")
    if params.gender == "girl" and params.name in BOY_NAMES:
        raise StoryError("Chosen name and gender do not match this world list.")
    if params.gender == "boy" and params.name in GIRL_NAMES:
        raise StoryError("Chosen name and gender do not match this world list.")


def predict_escalation(world: World, child: Entity, trouble: Trouble) -> bool:
    sim = world.copy()
    _touch_wound(sim, sim.get(child.id), trouble, narrate=False)
    return sim.get(child.id).memes.get("conflict", 0.0) >= THRESHOLD


def _touch_wound(world: World, child: Entity, trouble: Trouble, narrate: bool = True) -> None:
    child.meters["touches"] = child.meters.get("touches", 0.0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.memes["repetition"] = child.memes.get("repetition", 0.0) + 1
    if child.meters["touches"] >= 2:
        child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    if narrate:
        world.say(
            f"{child.id} kept peeking at the bandage one more time, as if looking again might answer the whole question."
        )


def _parent_warns(world: World, parent: Entity, child: Entity, trouble: Trouble) -> None:
    child.memes["warned"] = child.memes.get("warned", 0.0) + 1
    world.say(
        f'"Please do not {trouble.risk}," {parent.pronoun("possessive")} {parent.type} said. '
        f'"Let the scrape rest."'
    )


def _show_nightingale(world: World) -> None:
    world.say(
        f"Outside {world.setting.bird_spot}, a nightingale sang the same bright little tune again, soft and steady."
    )
    world.facts["nightingale_sings"] = True


def _r_conflict(world: World) -> list[str]:
    out = []
    for child in world.characters():
        if child.memes.get("conflict", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(
            f"{child.id} frowned and wanted one more look, but that only made the little fight in the room feel bigger."
        )
    return out


def _r_pus(world: World) -> list[str]:
    out = []
    child = world.get(world.facts["child"].id)
    trouble = world.facts["trouble"]
    if child.meters.get("touches", 0.0) < 2:
        return out
    sig = ("pus", child.id, trouble.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["pus"] = child.meters.get("pus", 0.0) + 1
    out.append("The scrape looked a little yellow at the edge, and that was the sort of thing that needed a gentle wash.")
    return out


CAUSAL_RULES = [
    _r_conflict,
    _r_pus,
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                if narrate:
                    for line in lines:
                        world.say(line)


def tell(setting: Setting, trouble: Trouble, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    wound = world.add(Entity(id="wound", type="thing", label="bandage"))
    bird = world.add(Entity(id="nightingale", type="thing", label="nightingale"))

    world.facts.update(child=child, parent=parent, wound=wound, bird=bird, trouble=trouble, setting=setting)

    # Act 1: ordinary day, tiny problem.
    world.say(f"{child.id} was a {trait} {gender} who noticed small things.")
    world.say(f"One afternoon, {child.id} {trouble.tiny_event}, and {parent.pronoun('possessive')} {parent.type} put a bandage on it.")
    world.say(f"{child.id} kept wanting to {trouble.repeated_action}, because the bandage looked strange.")

    # Act 2: repetition, curiosity, and the start of conflict.
    world.para()
    if not setting.indoors:
        world.day_time = "evening"
    _show_nightingale(world)
    _touch_wound(world, child, trouble)
    _touch_wound(world, child, trouble)
    _parent_warns(world, parent, child, trouble)
    propagate(world, narrate=True)

    # Act 3: a calmer routine and a softer ending.
    world.para()
    child.memes["conflict"] = 0.0
    world.say(
        f"{parent.id} washed the scrape with warm water, tucked on a clean bandage, and said it was best to leave the sore alone."
    )
    world.say(
        f"{child.id} nodded, watched the nightingale's song come back once more, and chose to listen instead of poke."
    )
    world.say(
        f"After that, the bandage stayed quiet, and the little room felt ordinary again."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    trouble = f["trouble"]
    return [
        f'Write a gentle slice-of-life story for a young child about {child.id}, a small wound, and the word "{trouble.keyword}".',
        f"Tell a story where {child.id} keeps checking a scrape too many times, a parent worries, and a nightingale sings outside.",
        f"Write a calm story about curiosity, repetition, and conflict that ends with a clean bandage and a bird song.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    trouble = f["trouble"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"What did {child.id} keep doing to the scrape?",
            answer=f"{child.id} kept checking it again and again, which made the worry repeat."
        ),
        QAItem(
            question=f"Why did {parent.id} get upset about the bandage?",
            answer=f"{parent.id} got upset because {child.id} kept touching the sore, and that could make the scrape hurt more and slow the healing."
        ),
        QAItem(
            question=f"What sound did the nightingale make while all this was happening?",
            answer="The nightingale sang a soft, steady tune that came back in the same gentle pattern."
        ),
        QAItem(
            question=f"What did the parent do at the end to help the wound at {place}?",
            answer=f"{parent.id} washed the scrape, put on a clean bandage, and helped {child.id} leave it alone."
        ),
    ]
    if f["child"].meters.get("pus", 0.0) >= THRESHOLD:
        qa.append(
            QAItem(
                question=f"Why was the yellow stuff on the bandage called a problem?",
                answer=f"The yellow stuff was pus, and it meant the sore needed careful cleaning instead of more poking."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nightingale?",
            answer="A nightingale is a small bird known for singing a clear, pretty song, often at dusk or night."
        ),
        QAItem(
            question="What is pus?",
            answer="Pus is a thick yellowish or whitish fluid that can appear when a sore is irritated or infected."
        ),
        QAItem(
            question="Why should a scrape be left alone after it is cleaned?",
            answer="A scrape should be left alone so the skin can heal and the bandage can keep it protected."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="kitchen", trouble="scrape", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="garden", trouble="scratch", name="Eli", gender="boy", parent="father", trait="thoughtful"),
]


ASP_RULES = r"""
% A trouble is valid when it is a small wound story with repetition and curiosity.
valid(Place, Trouble) :- setting(Place), trouble(Trouble).

% The conflict is structurally required in this slice-of-life world.
needs_conflict(Trouble) :- trouble(Trouble), requires(Trouble, conflict).

% Nightingale is a constant companion in every story in this world.
has_nightingale(Place) :- setting(Place), bird_spot(Place).

#show valid/2.
#show has_nightingale/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        lines.append(asp.fact("bird_spot", pid))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for tag in sorted(trouble.tags):
            lines.append(asp.fact("requires", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection() -> str:
    return "No story: this world only tells gentle small-wound scenes with repetition, curiosity, conflict, and a nightingale."


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    reasonableness_gate(StoryParams(
        place=args.place or "kitchen",
        trouble=args.trouble or "scrape",
        name=args.name or "Maya",
        gender=args.gender or "girl",
        parent=args.parent or "mother",
        trait=args.trait or "curious",
    ))
    combos = valid_combos()
    if args.place is not None:
        combos = [c for c in combos if c[0] == args.place]
    if args.trouble is not None:
        combos = [c for c in combos if c[1] == args.trouble]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or select_name(gender, rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trouble=trouble, name=name, gender=gender, parent=parent, trait=trait)


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.trouble not in TROUBLES:
        raise StoryError(explain_rejection())
    world = tell(SETTINGS[params.place], TROUBLES[params.trouble], params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/2.\n#show has_nightingale/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2. #show has_nightingale/1."))
        print(f"{len(asp.atoms(model, 'valid'))} valid combos")
        for place, trouble in asp.atoms(model, "valid"):
            print(f"  {place} {trouble}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.trouble} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
