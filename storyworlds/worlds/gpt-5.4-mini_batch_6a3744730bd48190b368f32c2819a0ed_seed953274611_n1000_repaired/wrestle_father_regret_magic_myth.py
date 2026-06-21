#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wrestle_father_regret_magic_myth.py
====================================================================

A small mythic storyworld: a child, a father, a magical object, a struggle,
regret, and a wise ending image.

This world keeps the simulation tiny and concrete:
- a child tries a risky act of wrestling a magic force or creature,
- the father warns, joins, or intervenes,
- regret appears when the act causes harm or fright,
- magic can be calm, wild, or wisely used,
- the ending proves what changed in the world state.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/wrestle_father_regret_magic_myth.py
    python storyworlds/worlds/gpt-5.4-mini/wrestle_father_regret_magic_myth.py --all
    python storyworlds/worlds/gpt-5.4-mini/wrestle_father_regret_magic_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/wrestle_father_regret_magic_myth.py --trace
    python storyworlds/worlds/gpt-5.4-mini/wrestle_father_regret_magic_myth.py --json
    python storyworlds/worlds/gpt-5.4-mini/wrestle_father_regret_magic_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    magic: bool = False
    living: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"father": "father", "mother": "mother"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    scene: str
    mythical: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class MagicForce:
    id: str
    label: str
    effect: str
    danger: int
    calm_method: str
    wise_phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    place: str
    force: str
    child_name: str
    child_gender: str
    father_name: str
    father_gender: str
    child_trait: str
    risk: str
    outcome: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_fear(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if child and child.meters["distress"] >= THRESHOLD and ("fear", "child") not in world.fired:
        world.fired.add(("fear", "child"))
        child.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_regret(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    father = world.entities.get("father")
    if child and father and child.meters["hurt"] >= THRESHOLD and ("regret", "child") not in world.fired:
        world.fired.add(("regret", "child"))
        child.memes["regret"] += 1
        father.memes["regret"] += 1
        out.append("__regret__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("regret", "social", _r_regret)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def myth_wrestle(world: World, child: Entity, father: Entity, force: MagicForce) -> None:
    child.meters["struggle"] += 1
    father.meters["strain"] += 1
    child.memes["boldness"] += 1
    world.say(
        f"In the old land of {world.facts['place'].label}, {child.id} and {father.id} "
        f"came to the edge of a magical trouble. {world.facts['place'].scene}"
    )
    world.say(
        f'The air shimmered with {force.label}, and {child.id} said, "I will wrestle it!"'
    )


def warn(world: World, father: Entity, child: Entity, force: MagicForce) -> None:
    father.memes["care"] += 1
    world.say(
        f'{father.id} took {child.pronoun("object")} by the shoulders. '
        f'"Be careful," {father.pronoun()} said. "Magic is not a toy. '
        f'If you wrestle it the wrong way, you may regret it."'
    )


def choose_wrestle(world: World, child: Entity, force: MagicForce) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'But {child.id} did not listen. {child.pronoun().capitalize()} reached '
        f'for the {force.label} and wrestled it with both hands.'
    )


def magic_turn(world: World, child: Entity, father: Entity, force: MagicForce) -> None:
    child.meters["hurt"] += 1
    child.meters["distress"] += 1
    father.meters["distress"] += 1
    world.say(
        f'The {force.label} flared bright. It twisted like a living ribbon and tossed '
        f'{child.id} back onto the moss.'
    )
    propagate(world, narrate=False)
    world.say(
        f"{force.effect.capitalize()}, and the green light faded as quickly as it had come."
    )


def regret_scene(world: World, child: Entity, father: Entity, force: MagicForce) -> None:
    world.say(
        f"{child.id} looked down and felt regret. {child.pronoun().capitalize()} "
        f"had wanted power, but had only made trouble."
    )
    world.say(
        f"{father.id} knelt beside {child.pronoun('object')} and said, "
        f'"We can still set this right."'
    )


def wise_fix(world: World, child: Entity, father: Entity, force: MagicForce) -> None:
    child.meters["hurt"] = 0
    child.meters["distress"] = 0
    father.meters["distress"] = 0
    child.memes["regret"] += 1
    child.memes["hope"] += 1
    father.memes["hope"] += 1
    world.say(
        f"{father.id} showed {child.id} the old way: {force.calm_method}. "
        f"The magic answered gently this time."
    )
    world.say(
        f"{force.wise_phrase.capitalize()}, and the bright trouble became a soft, "
        f"safe glow in {father.id}'s palm."
    )
    world.say(
        f"At the end, {child.id} and {father.id} walked home under the stars, "
        f"carrying no fear, only the lesson."
    )


def tell(place: Place, force: MagicForce, params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    father = world.add(Entity(id=params.father_name, kind="character", type=params.father_gender, role="father"))
    world.add(Entity(id="magic", type="thing", label=force.label, magic=True))
    world.facts["place"] = place
    world.facts["force"] = force
    world.facts["outcome"] = params.outcome

    myth_wrestle(world, child, father, force)
    world.para()
    warn(world, father, child, force)

    if params.outcome == "averted":
        child.memes["obedience"] += 1
        world.say(
            f"{child.id} stopped at once. Instead of wrestling the magic, {child.id} "
            f"watched {father.id} shape it into a harmless light."
        )
        wise_fix(world, child, father, force)
    else:
        choose_wrestle(world, child, force)
        world.para()
        magic_turn(world, child, father, force)
        regret_scene(world, child, father, force)
        world.para()
        wise_fix(world, child, father, force)

    world.facts.update(child=child, father=father)
    return world


PLACES = {
    "hills": Place(id="hills", label="the windy hills", scene="The hills were wide and old, with grass like green fire."),
    "cave": Place(id="cave", label="the echoing cave", scene="The cave sang back every footstep, as if the stones remembered names."),
    "shore": Place(id="shore", label="the shining shore", scene="The sea breathed at the rocks, and silver foam curled like the hem of a robe."),
}

FORCES = {
    "lantern-spirit": MagicForce(
        id="lantern-spirit",
        label="a lantern spirit",
        effect="the spirit flashed up like a startled star",
        danger=2,
        calm_method="his father breathed slowly and covered the flame with a cupped hand",
        wise_phrase="the spirit settled when it was treated with patience",
        tags={"magic", "light"},
    ),
    "golden-boar": MagicForce(
        id="golden-boar",
        label="a golden boar of spellfire",
        effect="the boar snorted sparks into the grass",
        danger=3,
        calm_method="his father traced a circle in the dirt and spoke the old stopping word",
        wise_phrase="the boar bowed its shining head",
        tags={"magic", "beast"},
    ),
    "river-knot": MagicForce(
        id="river-knot",
        label="a knot of river-magic",
        effect="the river-magic leapt like wet ropes",
        danger=2,
        calm_method="his father sang the untying song his own father taught him",
        wise_phrase="the knot loosened and flowed peacefully away",
        tags={"magic", "water"},
    ),
}

CHILDREN = [("Ari", "boy"), ("Mira", "girl"), ("Niko", "boy"), ("Sera", "girl")]
FATHERS = [("Father", "father"), ("Borin", "father"), ("Eamon", "father"), ("Orin", "father")]
TRAITS = ["brave", "curious", "fierce", "restless", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for f in FORCES:
            for _name, _gender in CHILDREN:
                combos.append((p, f, "story"))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts["force"]
    p = world.facts["place"]
    return [
        f'Write a mythic story for a young child about a father, a child, and {f.label}. Include the words "wrestle" and "regret".',
        f"Tell a myth where someone tries to wrestle {f.label} in {p.label} and learns a wiser use of magic.",
        f'Create a short legend with a father who warns his child that magic can bring regret if it is wrestled with carelessly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    father = world.facts["father"]
    force = world.facts["force"]
    qa = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {child.id} and {father.id}, who stood together at the edge of {world.facts['place'].label}. The story focused on their struggle with {force.label}.",
        ),
        QAItem(
            question="Why did the child feel regret?",
            answer=f"{child.id} felt regret after wrestling {force.label} and getting hurt. The magic answered wildly at first, so {child.id} wished the choice had been wiser.",
        ),
        QAItem(
            question="What did the father do at the end?",
            answer=f"{father.id} calmed the magic and taught a safer way to use it. That turned the danger into a gentle glow and left the child with a lesson instead of a wound.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    force = world.facts["force"]
    return [
        QAItem(
            question="What is magic in a mythic story?",
            answer="Magic is a strange power that can change light, fire, water, or the shapes of things. In myths it often feels older than people and must be handled with respect.",
        ),
        QAItem(
            question="Why should someone be careful with magic?",
            answer=f"Because magic can grow stronger than expected and hurt someone who rushes it. {force.label} showed that a bold choice can become trouble very quickly.",
        ),
        QAItem(
            question="What does regret mean?",
            answer="Regret is the sad feeling you get when you wish you had chosen differently. It often comes after a mistake or a hurtful decision.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.magic:
            bits.append("magic=True")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="hills", force="lantern-spirit", child_name="Ari", child_gender="boy", father_name="Borin", father_gender="father", child_trait="brave", risk="light", outcome="contained"),
    StoryParams(place="cave", force="golden-boar", child_name="Mira", child_gender="girl", father_name="Eamon", father_gender="father", child_trait="curious", risk="beast", outcome="contained"),
    StoryParams(place="shore", force="river-knot", child_name="Niko", child_gender="boy", father_name="Orin", father_gender="father", child_trait="restless", risk="water", outcome="averted"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this combination does not make a mythic struggle.)"


def outcome_of(params: StoryParams) -> str:
    return params.outcome


def ASP_RULES() -> str:
    return r"""
valid(P,F) :- place(P), force(F).
outcome(averted) :- chosen_outcome(averted).
outcome(contained) :- chosen_outcome(contained).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for f in FORCES:
        lines.append(asp.fact("force", f))
    for o in ("averted", "contained"):
        lines.append(asp.fact("chosen_outcome", o))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
        if clingo_set == python_set:
            print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        else:
            rc = 1
            print("MISMATCH between clingo and python valid_combos.")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with father, wrestle, regret, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--force", choices=FORCES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--father-name")
    ap.add_argument("--outcome", choices=["averted", "contained"])
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
    if args.outcome and args.outcome not in {"averted", "contained"}:
        raise StoryError("Invalid outcome.")
    place = args.place or rng.choice(list(PLACES))
    force = args.force or rng.choice(list(FORCES))
    child_name, child_gender = (args.child_name, args.child_gender) if args.child_name and args.child_gender else rng.choice(CHILDREN)
    father_name = args.father_name or rng.choice([n for n, _ in FATHERS])
    outcome = args.outcome or rng.choice(["averted", "contained"])
    return StoryParams(
        place=place,
        force=force,
        child_name=child_name,
        child_gender=child_gender,
        father_name=father_name,
        father_gender="father",
        child_trait=rng.choice(TRAITS),
        risk="magic",
        outcome=outcome,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.force not in FORCES:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], FORCES[params.force], params)
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
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for c in valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
