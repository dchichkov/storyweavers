#!/usr/bin/env python3
"""
storyworlds/worlds/bit_hominy_treaty_magic_detective_story.py
==============================================================

A tiny detective story world with magical clues, a bite of hominy, and a treaty
that can be kept or broken.

Premise:
- A child detective investigates a strange event in a small town.
- A magical bit of hominy acts as the odd clue that starts the case.
- A treaty between two neighbors is at risk when someone tampers with the clue.
- The detective uses careful observation, a charm, and one honest question to
  uncover the truth and restore the treaty.

The prose is driven by simulated world state:
- clues have physical meters (seen, moved, spilled, enchanted)
- people have emotional memes (curiosity, worry, trust, relief)
- the ending changes because the detective resolves the case, not because the
  paragraph is frozen and names are swapped.
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
    keeper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "woman", "mother", "mom", "detective-girl"}
        male = {"boy", "man", "father", "dad", "detective-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool = False
    magic_level: int = 1
    hush: str = "quiet"


@dataclass
class Case:
    mystery: str
    clue: str
    clue_phrase: str
    crime: str
    twist: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    effect: str
    use_line: str
    fixes: set[str] = field(default_factory=set)


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
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _case_turn(world: World) -> list[str]:
    out: list[str] = []
    suspect = world.facts["suspect"]
    clue = world.facts["clue"]
    detective = world.facts["detective"]
    if suspect.meters.get("tamper", 0.0) >= THRESHOLD and clue.meters.get("seen", 0.0) < THRESHOLD:
        sig = ("turn", suspect.id, clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            suspect.memes["nervous"] = suspect.memes.get("nervous", 0.0) + 1
            detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
            out.append(f"The clue looked wrong, and the case grew stranger.")
    return out


def _case_resolve(world: World) -> list[str]:
    out: list[str] = []
    detective = world.facts["detective"]
    suspect = world.facts["suspect"]
    treaty = world.facts["treaty"]
    clue = world.facts["clue"]
    charm = world.facts["charm"]
    if clue.meters.get("seen", 0.0) >= THRESHOLD and clue.meters.get("enchanted", 0.0) >= THRESHOLD:
        sig = ("resolve", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            treaty.meters["broken"] = 0
            treaty.meters["kept"] = 1
            detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
            suspect.memes["trust"] = suspect.memes.get("trust", 0.0) + 1
            out.append(f"The charm settled the magic, and the treaty could hold again.")
    return out


RULES = [
    _case_turn,
    _case_resolve,
]


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


def inspect_clue(world: World, detective: Entity, clue: Entity) -> None:
    clue.meters["seen"] = clue.meters.get("seen", 0.0) + 1
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    world.say(f"{detective.noun().capitalize()} studied the clue and noticed its odd shimmer.")


def use_charm(world: World, detective: Entity, charm: Charm, clue: Entity) -> None:
    clue.meters["enchanted"] = clue.meters.get("enchanted", 0.0) + 1
    world.say(f"{detective.noun().capitalize()} used the {charm.label}. {charm.use_line}")


def question_suspect(world: World, detective: Entity, suspect: Entity, treaty: Entity) -> None:
    suspect.memes["worry"] = suspect.memes.get("worry", 0.0) + 1
    detective.memes["serious"] = detective.memes.get("serious", 0.0) + 1
    world.say(
        f"{detective.noun().capitalize()} asked a careful question about the treaty, and {suspect.noun()} looked down."
    )


def reveal(world: World, detective: Entity, suspect: Entity, case: Case) -> None:
    suspect.meters["tamper"] = suspect.meters.get("tamper", 0.0) + 1
    world.say(
        f"The truth came out: {suspect.noun()} had touched the magical bit of hominy, but only to protect the treaty from a bigger mistake."
    )
    world.say(f"That was the twist: {case.twist}")


def tell_case(setting: Setting, case: Case, detective_name: str = "Mina", suspect_name: str = "Perry") -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name, kind="character", type="detective-girl",
        label=detective_name, phrase=f"young detective {detective_name}",
        meters={}, memes={"curiosity": 1.0, "care": 1.0}, tags={"detective"}
    ))
    suspect = world.add(Entity(
        id=suspect_name, kind="character", type="neighbor",
        label=suspect_name, phrase=f"neighbor {suspect_name}",
        meters={}, memes={"worry": 1.0}, tags={"neighbor"}
    ))
    treaty = world.add(Entity(
        id="treaty", kind="thing", type="treaty", label="treaty",
        phrase="the town treaty", meters={"kept": 1.0}, tags={"treaty"}
    ))
    clue = world.add(Entity(
        id="clue", kind="thing", type="hominy", label="bit of hominy",
        phrase=case.clue_phrase, meters={"seen": 0.0, "enchanted": 0.0},
        tags={"bit", "hominy", "magic"}
    ))
    charm = Charm(
        id="charm",
        label="moon-salt charm",
        effect="reveal hidden traces",
        use_line="A silver spark ran over the kernels, and the hidden magic showed itself.",
        fixes={"magic"},
    )

    world.facts.update(
        detective=detective,
        suspect=suspect,
        treaty=treaty,
        clue=clue,
        charm=charm,
        case=case,
        setting=setting,
    )

    world.say(f"In {setting.place}, the hush was so quiet that every footstep sounded like a clue.")
    world.say(f"{detective.noun().capitalize()} was a child detective who loved hard puzzles and honest answers.")
    world.say(f"The case began with a {case.clue} near the treaty desk: {case.clue_phrase}.")
    world.say(f"Everyone said the {case.crime}, and that made the treaty feel shaky.")

    world.para()
    inspect_clue(world, detective, clue)
    question_suspect(world, detective, suspect, treaty)
    propagate(world)

    world.para()
    world.say(f"{detective.noun().capitalize()} saw the magic hiding inside the clue and chose the right charm.")
    use_charm(world, detective, charm, clue)
    reveal(world, detective, suspect, case)
    propagate(world)

    world.para()
    world.say(
        f"In the end, the treaty stayed whole, the strange bit of hominy stopped glowing, and {detective.noun()} walked home with the case solved."
    )
    world.say(case.resolution)

    return world


SETTINGS = {
    "square": Setting(place="the market square", indoors=False, magic_level=1, hush="busy"),
    "library": Setting(place="the old library", indoors=True, magic_level=2, hush="quiet"),
    "dock": Setting(place="the moonlit dock", indoors=False, magic_level=3, hush="salt-still"),
}


CASES = {
    "treaty": Case(
        mystery="a treaty between two neighbors was in danger",
        clue="strange bit of hominy",
        clue_phrase="a tiny golden kernel that sparkled like it had a secret",
        crime="someone had hidden the treaty seal",
        twist="the hominy had been enchanted to point toward the seal, not to steal it",
        resolution="The neighbors signed the treaty again, and everyone promised to tell the truth before fear could grow.",
        tags={"treaty", "hominy", "bit", "magic"},
    ),
    "seal": Case(
        mystery="a treaty seal had vanished from a desk",
        clue="magic hominy crumb",
        clue_phrase="one warm crumb of hominy with a blue glint in it",
        crime="someone had moved the seal to protect it from a quarrel",
        twist="the crumb was a magical marker, left so the detective could follow the trail",
        resolution="The treaty was restored, and the desk looked neat and calm again.",
        tags={"treaty", "hominy", "bit", "magic"},
    ),
}

CHARM = Charm(
    id="moon-salt",
    label="moon-salt charm",
    effect="show hidden magic",
    use_line="A thin silver shine ran over the clue, and the secret trail woke up.",
    fixes={"magic"},
)


@dataclass
class StoryParams:
    setting: str
    case: str
    detective: str
    suspect: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CASES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small magical detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective")
    ap.add_argument("--suspect")
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
    combos = valid_combos()
    if args.setting and args.case and (args.setting, args.case) not in combos:
        raise StoryError("That setting and case do not belong together.")
    setting = args.setting or rng.choice([s for s, _ in combos])
    case = args.case or rng.choice([c for s, c in combos if s == setting])
    detective = args.detective or rng.choice(["Mina", "Iris", "Jules", "Nora", "Theo"])
    suspect = args.suspect or rng.choice(["Perry", "Lena", "Rafi", "Bess", "Otis"])
    if detective == suspect:
        raise StoryError("The detective and the suspect must be different people.")
    return StoryParams(setting=setting, case=case, detective=detective, suspect=suspect)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child that includes "bit", "hominy", and "treaty", and has a little magic clue.',
        f"Tell a gentle mystery story set in {f['setting'].place} about {f['detective'].noun()} solving a treaty problem with a magical bit of hominy.",
        f"Write a child-friendly detective tale where a clue glows, a treaty is at risk, and the truth helps everyone feel safe again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    suspect: Entity = f["suspect"]
    treaty: Entity = f["treaty"]
    clue: Entity = f["clue"]
    case: Case = f["case"]
    return [
        QAItem(
            question=f"What kind of story is this about {detective.noun()} and the strange bit of hominy?",
            answer=f"It is a detective story. {detective.noun().capitalize()} follows a magical clue to understand what happened to the treaty.",
        ),
        QAItem(
            question=f"What was special about the {clue.label} at the start?",
            answer=f"It was a magical bit of hominy, and it shimmered like it had a secret to share.",
        ),
        QAItem(
            question=f"Why did the treaty feel shaky?",
            answer=f"The treaty felt shaky because something was wrong in the case, and nobody yet knew the truth.",
        ),
        QAItem(
            question=f"How did {detective.noun()} solve the mystery?",
            answer=f"{detective.noun().capitalize()} studied the clue, used a charm to wake up the magic, and asked careful questions until the truth came out.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The treaty stayed whole again, the clue stopped being mysterious, and everyone could trust one another more.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a treaty?",
            answer="A treaty is an agreement people make so they can live or work together peacefully.",
        ),
        QAItem(
            question="What is hominy?",
            answer="Hominy is corn that has been prepared until the kernels get plump and soft.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something impossible in real life that can happen in a story, like a clue that glows or reveals secrets.",
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_has_magic(C) :- clue(C), tagged(C, magic).
treaty_at_risk(T) :- treaty(T), broken(T).
needs_deduction(D, C) :- detective(D), clue(C), clue_has_magic(C).
solved(D, T) :- detective(D), treaty(T), clue(C), clue_has_magic(C), revealed(C), kept(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CASES:
        lines.append(asp.fact("case", c))
    lines.append(asp.fact("detective", "mina"))
    lines.append(asp.fact("clue", "hominy"))
    lines.append(asp.fact("treaty", "town"))
    lines.append(asp.fact("tagged", "hominy", "magic"))
    lines.append(asp.fact("revealed", "hominy"))
    lines.append(asp.fact("kept", "town"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/2."))
    asp_solved = set(asp.atoms(model, "solved"))
    py_solved = {("mina", "town")}
    if asp_solved == py_solved:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(asp_solved))
    print("PY :", sorted(py_solved))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show needs_deduction/2."))
    return sorted(set(asp.atoms(model, "needs_deduction")))


def generate(params: StoryParams) -> StorySample:
    world = tell_case(SETTINGS[params.setting], CASES[params.case], params.detective, params.suspect)
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
    StoryParams(setting="library", case="treaty", detective="Mina", suspect="Perry"),
    StoryParams(setting="square", case="seal", detective="Iris", suspect="Lena"),
    StoryParams(setting="dock", case="treaty", detective="Jules", suspect="Rafi"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show needs_deduction/2."))
        items = sorted(set(asp.atoms(model, "needs_deduction")))
        print(f"{len(items)} compatible detective cases:")
        for d, c in items:
            print(f"  {d} -> {c}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.case} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
