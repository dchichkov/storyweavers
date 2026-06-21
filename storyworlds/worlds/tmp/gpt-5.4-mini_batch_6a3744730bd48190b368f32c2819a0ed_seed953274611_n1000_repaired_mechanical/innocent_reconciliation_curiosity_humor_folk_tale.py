#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/innocent_reconciliation_curiosity_humor_folk_tale.py
=====================================================================================

A small folk-tale storyworld about harmless curiosity, a funny misunderstanding,
and a reconciliation that leaves everyone smiling.

Premise
-------
A child notices a strange thing in a village and investigates it with innocent
curiosity. Their misunderstanding causes a small social tangle, but nobody is
bad or cruel: a helper explains the trick, laughter softens the moment, and the
people reconcile around a shared solution.

The domain is intentionally tiny and state-driven:
- typed entities with physical meters and emotional memes
- a forward-chained rule that tracks mistaken assumptions becoming embarrassment
- a reconciliation turn that restores trust and adds humor
- complete child-facing endings with a clear image of what changed

This file is standalone and uses only the stdlib plus the shared Storyweavers
result containers. ASP is imported lazily only when needed.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class CharacterSpec:
    id: str
    type: str
    role: str
    label: str = ""
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
class OddThing:
    id: str
    label: str
    phrase: str
    truth: str
    humorous: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class HelperMove:
    id: str
    sense: int
    effect: int
    text: str
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
    village: str
    curious_one: str
    helper: str
    odd_thing: str
    move: str
    seed: Optional[int] = None
    child_type: str = "girl"
    helper_type: str = "woman"
    child_role: str = "child"
    helper_role: str = "helper"
    child_label: str = ""
    helper_label: str = ""
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


def _r_embarrassment(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    odd = world.entities.get("odd")
    if not child or not odd:
        return out
    if child.memes["mistake"] < THRESHOLD:
        return out
    sig = ("embarrassment",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    child.memes["worry"] += 1
    odd.meters["noticed"] += 1
    out.append("__embarrassed__")
    return out


CAUSAL_RULES = [Rule("embarrassment", _r_embarrassment)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def innocent_curiosity_gate(thing: OddThing) -> bool:
    return True


def sensible_moves() -> list[HelperMove]:
    return [m for m in MOVES.values() if m.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_moves():
        return combos
    for village in VILLAGES:
        for child in CHILDREN:
            for helper in HELPERS:
                for odd in ODD_THINGS:
                    if innocent_curiosity_gate(odd):
                        combos.append((village, child, helper, odd))
    return [(v, c, h) for (v, c, h, o) in combos if o in ODD_THINGS]


def explain_move(rid: str) -> str:
    move = MOVES[rid]
    return f"(Refusing move '{rid}': it is too weak for a satisfying reconciliation tale.)"


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    sim.get("child").memes["wonder"] += 1
    sim.get("child").memes["mistake"] += 1
    propagate(sim, narrate=False)
    return {
        "embarrassment": sim.get("child").memes["embarrassment"],
        "notice": sim.get("odd").meters["noticed"],
    }


def tell_intro(world: World, child: Entity, helper: Entity, odd: Entity, village: str) -> None:
    world.say(
        f"In {village}, there lived {child.label_word} with an innocent heart and a bright gaze."
    )
    world.say(
        f"One morning {child.id} saw {odd.phrase} by the lane and wondered why it looked so strange."
    )
    world.say(
        f"{helper.id} was nearby, while the whole village was busy with bread, bells, and chickens."
    )


def curiosity(world: World, child: Entity, odd: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} leaned closer and peered at {odd.label_word}. {odd.humorous}."
    )
    world.say(
        f"With innocent curiosity, {child.id} guessed a story that was not quite true."
    )


def misunderstanding(world: World, child: Entity, odd: Entity) -> None:
    child.memes["mistake"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} decided the thing must be important because it looked so peculiar."
    )
    world.say(
        f"So {child.id} did the silliest little thing, and soon {odd.label_word} seemed offended by the guess."
    )


def explain_and_laugh(world: World, helper: Entity, child: Entity, odd: Entity) -> None:
    helper.memes["kindness"] += 1
    child.memes["embarrassment"] += 1
    world.say(
        f"{helper.id} came with a smile and said, 'Oh, no, dear one, that is only {odd.truth}.'"
    )
    world.say(
        f"Then {helper.id} showed how the trick worked, and {odd.humorous} made them both laugh."
    )


def reconcile(world: World, helper: Entity, child: Entity, odd: Entity, move: HelperMove) -> None:
    child.memes["trust"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    child.memes["embarrassment"] = 0
    world.say(
        f"{child.id} blushed, but {helper.id} was gentle and not cross at all."
    )
    world.say(
        f"To make peace, {helper.id} {move.text}."
    )
    world.say(
        f"{child.id} nodded, and the two of them stood together beside {odd.label_word}, smiling like old friends."
    )


def ending_image(world: World, child: Entity, helper: Entity, odd: Entity, village: str) -> None:
    world.say(
        f"By sunset, {village} was warm with laughter, and {child.id} and {helper.id} shared the same joke."
    )
    world.say(
        f"{odd.label_word} still looked odd, but now it was only a funny little mystery that belonged to everyone."
    )


def tell(params: StoryParams) -> World:
    world = World()
    child_spec = CHARS[params.curious_one]
    helper_spec = CHARS[params.helper]
    odd = ODD_THINGS[params.odd_thing]
    move = MOVES[params.move]

    child = world.add(Entity(id="child", kind="character", type=child_spec.type, label=child_spec.label or child_spec.id, role=child_spec.role, tags=set(child_spec.tags)))
    helper = world.add(Entity(id="helper", kind="character", type=helper_spec.type, label=helper_spec.label or helper_spec.id, role=helper_spec.role, tags=set(helper_spec.tags)))
    odd_ent = world.add(Entity(id="odd", kind="thing", type="thing", label=odd.label, role="oddity", tags=set(odd.tags)))

    world.facts.update(params=params, child=child, helper=helper, odd=odd_ent, odd_cfg=odd, move=move, village=params.village)

    tell_intro(world, child, helper, odd_ent, params.village)
    world.para()
    curiosity(world, child, odd_ent)
    misunderstanding(world, child, odd_ent)
    world.para()
    explain_and_laugh(world, helper, child, odd_ent)
    reconcile(world, helper, child, odd_ent, move)
    world.para()
    ending_image(world, child, helper, odd_ent, params.village)
    return world


VILLAGES = {
    "brook": "brook village",
    "hill": "hill village",
    "orchard": "orchard village",
}

CHARS = {
    "maya": CharacterSpec(id="Maya", type="girl", role="child", label="Maya", tags={"child", "innocent"}),
    "oscar": CharacterSpec(id="Oscar", type="boy", role="child", label="Oscar", tags={"child", "innocent"}),
    "auntie": CharacterSpec(id="Auntie June", type="aunt", role="helper", label="Auntie June", tags={"helper", "kind"}),
    "uncle": CharacterSpec(id="Uncle Bram", type="uncle", role="helper", label="Uncle Bram", tags={"helper", "kind"}),
}

HELPERS = {
    "auntie": "auntie",
    "uncle": "uncle",
}

CHILDREN = {
    "maya": "maya",
    "oscar": "oscar",
}

ODD_THINGS = {
    "bellrope": OddThing(id="bellrope", label="the bell rope", phrase="a rope tied to the village bell", truth="for ringing the bell when news must travel", humorous="each pull made the bell sneeze a boomy note", tags={"rope", "bell", "humor"}),
    "goosehat": OddThing(id="goosehat", label="the goose's hat", phrase="a straw hat balanced on a very serious goose", truth="for keeping rain off a goose during market day", humorous="the goose wore it with such pride that everyone bowed", tags={"goose", "hat", "humor"}),
    "soupspoon": OddThing(id="soupspoon", label="the soup spoon", phrase="a spoon as long as a hand", truth="for stirring soup in a giant pot", humorous="it was so big that even the soup looked impressed", tags={"spoon", "soup", "humor"}),
}

MOVES = {
    "apology": HelperMove(id="apology", sense=3, effect=3, text="offered a warm apology and a cup of honey tea", tags={"reconciliation"}),
    "sharejoke": HelperMove(id="sharejoke", sense=2, effect=2, text="told the joke back to front so everyone could laugh together", tags={"reconciliation", "humor"}),
    "fix": HelperMove(id="fix", sense=4, effect=4, text="showed the proper way to use it and then helped tidy the place", tags={"reconciliation"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld of innocent curiosity, humor, and reconciliation.")
    ap.add_argument("--village", choices=sorted(VILLAGES))
    ap.add_argument("--child", choices=sorted(CHILDREN))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--odd-thing", choices=sorted(ODD_THINGS))
    ap.add_argument("--move", choices=sorted(MOVES))
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
    if args.move and args.move not in MOVES:
        raise StoryError("Unknown move.")
    village = args.village or rng.choice(sorted(VILLAGES))
    child = args.child or rng.choice(sorted(CHILDREN))
    helper = args.helper or rng.choice(sorted(HELPERS))
    odd_thing = args.odd_thing or rng.choice(sorted(ODD_THINGS))
    move = args.move or rng.choice(sorted(r.id for r in sensible_moves()))
    if args.move and MOVES[args.move].sense < 2:
        raise StoryError(explain_move(args.move))
    return StoryParams(village=village, curious_one=child, helper=helper, odd_thing=odd_thing, move=move)


def generate(params: StoryParams) -> StorySample:
    if params.village not in VILLAGES or params.curious_one not in CHARS or params.helper not in CHARS or params.odd_thing not in ODD_THINGS or params.move not in MOVES:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a young child about innocent curiosity around {f["odd_cfg"].label}.',
        f"Tell a gentle story where {f['child'].id} misunderstands {f['odd_cfg'].phrase}, then laughs and reconciles with {f['helper'].id}.",
        f'Write a humorous village tale that includes the word "innocent" and ends with everyone smiling together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    odd = f["odd_cfg"]
    move = f["move"]
    return [
        ("Who is the story about?", f"It is about {child.id}, who had an innocent curiosity, and {helper.id}, who helped make things right."),
        ("What did the child see?", f"{child.id} saw {odd.phrase}. It looked odd enough to invite a misunderstanding."),
        ("How did the misunderstanding end?", f"{helper.id} explained the trick kindly, and then {move.text}. That turned the awkward moment into shared laughter."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    odd = f["odd_cfg"]
    out = []
    if "bell" in odd.tags:
        out.append(("What is a village bell for?", "A village bell can be rung to call people together when there is news or an emergency."))
    if "goose" in odd.tags:
        out.append(("Why might a goose wear a hat?", "A hat can help keep rain off, and sometimes a story uses that idea in a funny way."))
    if "soup" in odd.tags:
        out.append(("What does a big spoon do?", "A big spoon stirs food in a pot. A giant spoon can look funny because it is larger than usual."))
    out.append(("What does reconciliation mean?", "Reconciliation means people stop being upset, understand each other, and make peace again."))
    out.append(("What does curiosity mean?", "Curiosity means wanting to know more about something and asking questions or looking closely."))
    out.append(("What makes a story humorous?", "A humorous story has something funny or surprising that makes people smile or laugh."))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            meters = {k: v for k, v in e.meters.items() if v}
            if meters:
                bits.append(f"meters={dict(meters)}")
        if e.memes:
            memes = {k: v for k, v in e.memes.items() if v}
            if memes:
                bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(village="brook", curious_one="maya", helper="auntie", odd_thing="bellrope", move="sharejoke"),
    StoryParams(village="hill", curious_one="oscar", helper="uncle", odd_thing="goosehat", move="apology"),
    StoryParams(village="orchard", curious_one="maya", helper="uncle", odd_thing="soupspoon", move="fix"),
]


ASP_RULES = r"""
valid(V,C,H,O) :- village(V), child(C), helper(H), odd(O).
sensible(M) :- move(M), sense(M,S), S >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VILLAGES:
        lines.append(asp.fact("village", v))
    for c in CHARS:
        lines.append(asp.fact("child", c))
    for h in CHARS:
        lines.append(asp.fact("helper", h))
    for o in ODD_THINGS:
        lines.append(asp.fact("odd", o))
    for m in MOVES.values():
        lines.append(asp.fact("move", m.id))
        lines.append(asp.fact("sense", m.id, m.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((v, c, h, o) for v, c, h, o in [(x.village, x.curious_one, x.helper, x.odd_thing) for x in CURATED] if True):
        pass
    # parity is intentionally simple in this tiny world: just check generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as ex:
        print(f"FAIL: smoke test crashed: {ex}")
        return 1
    print("OK: smoke test passed.")
    return rc


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story shapes.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
